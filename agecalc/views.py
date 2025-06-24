from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date


@login_required
def age_form(request):
    age = None
    name = ''
    birthday = ''
    if request.method == 'POST':
        name = request.POST.get('name', '')
        birthday = request.POST.get('birthday', '')
        if birthday:
            try:
                born = date.fromisoformat(birthday)
                today = date.today()
                age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            except ValueError:
                age = None
    return render(request, 'agecalc/age_form.html', {'age': age, 'name': name, 'birthday': birthday})
