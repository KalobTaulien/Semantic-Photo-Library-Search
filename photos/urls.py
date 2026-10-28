from django.urls import path

from . import views

app_name = "photos"

urlpatterns = [
    path("", views.library, name="library"),
    path("upload/", views.upload, name="upload"),
    path("<int:pk>/status/", views.photo_status, name="photo_status"),
]
