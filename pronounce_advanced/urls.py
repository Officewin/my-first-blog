from django.urls import path
from . import views

urlpatterns = [
    path('', views.pronounce, name='pronounce_advanced'),
    path('history/', views.history, name='pronounce_advanced_history'),
]
