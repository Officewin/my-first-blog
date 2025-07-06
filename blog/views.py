"""Blog views for posts and interview features."""

try:
    import requests
except ImportError:  # pragma: no cover - handled at runtime
    requests = None

from django.http import JsonResponse
from django.shortcuts import render

from .models import Resume


def post_list(request):
    return render(request, 'blog/post_list.html', {})


def interview(request):
    """Render the interview preparation page."""
    return render(request, 'blog/interview.html', {})


def upload_resume(request):
    """Handle resume PDF upload and parse via microservice."""
    if not requests:
        return JsonResponse(
            {'error': 'requests library is not installed'},
            status=500,
        )

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        try:
            resp = requests.post(
                'http://localhost:3000/parse',
                files={'file': uploaded_file}
            )
            resp.raise_for_status()
            parsed = resp.json()
        except Exception:
            return JsonResponse({'error': 'Parsing failed'}, status=500)
        resume = Resume.objects.create(
            user=request.user if request.user.is_authenticated else None,
            file=uploaded_file,
            parsed_data=parsed,
        )
        return JsonResponse(resume.parsed_data)
    return JsonResponse({'error': 'Invalid request'}, status=400)
