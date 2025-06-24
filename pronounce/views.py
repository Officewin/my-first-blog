import random
from pathlib import Path
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
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


@csrf_exempt
def pronounce(request):
    if request.method == 'POST':
        text = request.POST.get('word')
        if not text:
            return JsonResponse({'error': 'Missing parameter: word'}, status=400)
        if 'audio' not in request.FILES:
            return JsonResponse({'error': 'Missing audio file'}, status=400)
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
                    resp = requests.post(
                        API_URL,
                        params=params,
                        data=params,
                        files=files,
                        timeout=10,
                    )
                    data = resp.json()
                except requests.exceptions.RequestException as e:
                    msg = getattr(e, 'response', None)
                    if msg is not None:
                        msg = f"{msg.status_code} {msg.reason}"
                    else:
                        msg = str(e)
                    raise URLError(msg)
            except ModuleNotFoundError:
                boundary = uuid.uuid4().hex
                body_parts = []
                for name, value in params.items():
                    body_parts.extend(
                        [f"--{boundary}", f"Content-Disposition: form-data; name=\"{name}\"", "", str(value)]
                    )
                for name, (filename, content, content_type) in files.items():
                    body_parts.extend(
                        [
                            f"--{boundary}",
                            f"Content-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"",
                            f"Content-Type: {content_type}",
                            "",
                            content,
                        ]
                    )
                body_parts.append(f"--{boundary}--")
                body_parts.append("")
                body_bytes = b"\r\n".join(
                    part if isinstance(part, bytes) else part.encode() for part in body_parts
                )
                query = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{API_URL}?{query}", data=body_bytes)
                req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())

            if data.get("status") != "ok":
                msg = data.get("detail_message", "Unknown error")
                return JsonResponse({"error": msg}, status=400)

            text_score = data.get("text_score", {})
            score = text_score.get("score") or text_score.get("score_percent")
            ielts = text_score.get("score_ielts") or text_score.get("score_pte")
            phone_scores = []
            for w in text_score.get("word_score_list", []):
                for ph in w.get("phone_score_list", []):
                    phone_scores.append(
                        {"phone": ph.get("phone"), "score": ph.get("score")}
                    )
            warning = ""
            if data.get("score_issue_list"):
                warning = ", ".join(data["score_issue_list"])

            return JsonResponse(
                {
                    "score": score,
                    "ielts": ielts,
                    "phonemes": phone_scores,
                    "warning": warning,
                }
            )
        except URLError as e:
            msg = getattr(e, "reason", str(e))
            return JsonResponse({"error": f"Network error: {msg}"}, status=502)
        except Exception as e:
            return JsonResponse({"error": f"Error: {e}"}, status=500)

    word = get_random_word()
    return render(request, 'pronounce/pronounce.html', {'word': word})
