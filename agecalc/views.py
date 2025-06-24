from django.shortcuts import render
from datetime import date


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
