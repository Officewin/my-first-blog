from django.urls import path
from . import views

urlpatterns = [
    path('', views.pronounce, name='pronounce'),
    path('history/', views.history, name='pronounce_history'),
]
