from django.urls import path
from . import views


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('interview/', views.interview, name='interview'),
]