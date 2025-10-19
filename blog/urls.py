from django.urls import path
from . import views


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('interview/', views.interview, name='interview'),
    path('upload-resume/', views.upload_resume, name='upload_resume'),
]
