import random
from pathlib import Path
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from .models import (
    PronunciationHistory,
    DailyPractice,
    DailySubmission,
    PracticeItem,
)
from django.db import OperationalError, transaction
import uuid
import urllib.request
from urllib.error import URLError
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent
WORD_FILE = BASE_DIR / 'sat_words.txt'
API_KEY = urllib.parse.unquote(
    'f01m%2BMrbKgPs26UhyQmyLl2Df4dfbkx75NHmEQF756Mbbq%2FOjd9t%2BsTgIdZjuvns%2BbrK0%2BoY7rYjZ35btIXwKOMafdWNx3GDo%2BY%2BnlozkEvPj56RD0i4SIFXqswFBNF%2F'
)
API_URL = 'https://api2.speechace.com/api/scoring/text/v9/json'


def get_random_word():
    words = WORD_FILE.read_text().splitlines()
    return random.choice(words)


def _daily_words(request):
    """Return today's practice word list and index, using DB for persistence."""
    today = timezone.now().date()
    try:
        word_list = list(PracticeItem.objects.values_list("text", flat=True))
        if word_list:
            choices = random.sample(word_list, min(10, len(word_list)))
        else:
            choices = random.sample(WORD_FILE.read_text().splitlines(), 10)
        record, created = DailyPractice.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={"words": choices, "index": 0},
        )
        return record.words, record.index, record
    except OperationalError:
        # Fallback to session storage if migrations not run
        session = request.session
        key_date = session.get("practice_date")
        if key_date != today.isoformat():
            words = WORD_FILE.read_text().splitlines()
            session["practice_words"] = random.sample(words, 10)
            session["practice_index"] = 0
            session["practice_date"] = today.isoformat()
        return (
            session["practice_words"],
            session.get("practice_index", 0),
            None,
        )


def _daily_submission(user):
    """Return today's submission record for the given user."""
    today = timezone.now().date()
    try:
        record, _ = DailySubmission.objects.get_or_create(
            user=user, date=today, defaults={"count": 0}
        )
        return record
    except OperationalError:
        return None


def reserve_daily_submission(user) -> bool:
    """Atomically increment today's submission count or deny if limit reached."""
    today = timezone.now().date()
    try:
        with transaction.atomic():
            record, _ = DailySubmission.objects.select_for_update().get_or_create(
                user=user, date=today, defaults={"count": 0}
            )
            if record.count >= 10:
                return False
            record.count += 1
            record.save(update_fields=["count"])
        return True
    except OperationalError:
        # Migrations might not be applied; allow submission but without limit
        return True


def _save_history(user, text: str, payload: str) -> None:
    """Persist a JSON payload if it can be parsed."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return
    if user.is_authenticated:
        try:
            PronunciationHistory.objects.create(
                user=user, text=text, response=data
            )
        except OperationalError:
            # Table might not exist if migrations haven't been run.
            pass


@csrf_exempt
@login_required
def pronounce(request):
    access = getattr(request.user, "app_access", None)
    if not access or not access.pronounce_easy:
        return HttpResponse("it is not allowed", status=403)
    words, index, record = _daily_words(request)
    sub_record = _daily_submission(request.user)

    if request.method == 'POST':
        if sub_record and sub_record.count >= 10:
            return HttpResponse('Daily submission limit reached.', status=400)
        if index >= len(words):
            return HttpResponse('Daily quota reached', status=400)
        text = request.POST.get('word')
        if not text:
            return HttpResponse('Missing parameter: word', status=400)
        expected = words[index]
        if text != expected:
            return HttpResponse('Unexpected word', status=400)
        if 'audio' not in request.FILES:
            return HttpResponse('Missing audio file', status=400)
        if not reserve_daily_submission(request.user):
            return HttpResponse('Daily submission limit reached.', status=400)
        audio = request.FILES['audio']
        files = {
            'user_audio_file': ('recording.wav', audio.read(), 'audio/wav'),
        }
        params = {
            'key': API_KEY,
            'dialect': 'en-us',
            'text': text,
            'user_text': text,
        }
        try:
            try:
                import requests
                try:
                    resp = requests.post(API_URL, params=params, data=params, files=files, timeout=10)
                    content = resp.text
                    _save_history(request.user, text, content)
                    if record:
                        record.index = index + 1
                        record.save(update_fields=["index"])
                    else:
                        request.session['practice_index'] = index + 1
                    return HttpResponse(content)
                except requests.exceptions.RequestException as e:
                    msg = getattr(e, 'response', None)
                    if msg is not None:
                        msg = f'{msg.status_code} {msg.reason}'
                    else:
                        msg = str(e)
                    raise URLError(msg)
            except ModuleNotFoundError:
                boundary = uuid.uuid4().hex
                body_parts = []
                for name, value in params.items():
                    body_parts.extend([
                        f'--{boundary}',
                        f'Content-Disposition: form-data; name="{name}"',
                        '',
                        str(value),
                    ])
                for name, (filename, content, content_type) in files.items():
                    body_parts.extend([
                        f'--{boundary}',
                        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"',
                        f'Content-Type: {content_type}',
                        '',
                        content,
                    ])
                body_parts.append(f'--{boundary}--')
                body_parts.append('')
                body_bytes = b"\r\n".join(
                    part if isinstance(part, bytes) else part.encode() for part in body_parts
                )
                query = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{API_URL}?{query}", data=body_bytes)
                req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read().decode()
                    _save_history(request.user, text, content)
                    if record:
                        record.index = index + 1
                        record.save(update_fields=["index"])
                    else:
                        request.session['practice_index'] = index + 1
                    return HttpResponse(content)
        except URLError as e:
            msg = getattr(e, 'reason', str(e))
            return HttpResponse(f'Network error: {msg}', status=502)
        except Exception as e:
            return HttpResponse(f'Error: {e}', status=500)

    if index >= len(words):
        return render(
            request,
            'pronounce_easy/pronounce.html',
            {'done': True, 'count': index, 'total': len(words)},
        )

    word = words[index]
    item = PracticeItem.objects.filter(text=word).first()
    return render(
        request,
        'pronounce_easy/pronounce.html',
        {
            'word': word,
            'count': index,
            'total': len(words),
            'item': item,
        },
    )


@login_required
def history(request):
    access = getattr(request.user, "app_access", None)
    if not access or not access.pronounce_easy:
        return HttpResponse("it is not allowed", status=403)
    migration_needed = False
    try:
        records = list(
            PronunciationHistory.objects.filter(user=request.user).order_by(
                "-created"
            )[:50]
        )
    except OperationalError:
        records = []
        migration_needed = True
    return render(
        request,
        "pronounce_easy/history.html",
        {"history": records, "migration_needed": migration_needed},
    )
