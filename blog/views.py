from django.shortcuts import render

def post_list(request):
    return render(request, 'blog/post_list.html', {})


def interview(request):
    """Render the interview preparation page."""
    return render(request, 'blog/interview.html', {})
