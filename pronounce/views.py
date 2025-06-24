import random
from pathlib import Path
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import uuid
import urllib.request

BASE_DIR = Path(__file__).resolve().parent
WORD_FILE = BASE_DIR / 'sat_words.txt'
API_KEY = 'f01m%2BMrbKgPs26UhyQmyLl2Df4dfbkx75NHmEQF756Mbbq%2FOjd9t%2BsTgIdZjuvns%2BbrK0%2BoY7rYjZ35btIXwKOMafdWNx3GDo%2BY%2BnlozkEvPj56RD0i4SIFXqswFBNF%2F'
API_URL = 'https://api2.speechace.com/api/scoring/text/v9/json'


def get_random_word():
    words = WORD_FILE.read_text().splitlines()
    return random.choice(words)


@csrf_exempt
def pronounce(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio = request.FILES['audio']
        text = request.POST.get('word', '')
        files = {
            'user_audio_file': ('recording.wav', audio.read(), 'audio/wav'),
        }
        data = {
            'key': API_KEY,
            'dialect': 'en-us',
            'text': text,
        }
        try:
            try:
                import requests
                resp = requests.post(API_URL, files=files, data=data, timeout=10)
                return HttpResponse(resp.text)
            except ModuleNotFoundError:
                boundary = uuid.uuid4().hex
                body_parts = []
                for name, (filename, content, content_type) in files.items():
                    body_parts.extend([
                        f'--{boundary}',
                        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"',
                        f'Content-Type: {content_type}',
                        '',
                        content,
                    ])
                for name, value in data.items():
                    body_parts.extend([
                        f'--{boundary}',
                        f'Content-Disposition: form-data; name="{name}"',
                        '',
                        value,
                    ])
                body_parts.append(f'--{boundary}--')
                body_parts.append('')
                body_bytes = b"\r\n".join(
                    part if isinstance(part, bytes) else part.encode() for part in body_parts
                )
                req = urllib.request.Request(API_URL, data=body_bytes)
                req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return HttpResponse(resp.read().decode())
        except Exception as e:
            return HttpResponse(f'Error: {e}', status=500)

    word = get_random_word()
    return render(request, 'pronounce/pronounce.html', {'word': word})
