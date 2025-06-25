from django.urls import path
from . import views

urlpatterns = [
    path('', views.pronounce, name='pronounce_easy'),
    path('history/', views.history, name='pronounce_easy_history'),
]
