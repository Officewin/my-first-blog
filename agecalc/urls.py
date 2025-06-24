from django.urls import path
from . import views

urlpatterns = [
    path('', views.age_form, name='age_form'),
]
