from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.conversation, name="conversation"),
    path("<int:pk>/", views.conversation, name="conversation"),
    path("<int:pk>/messages/", views.send_message, name="send_message"),
]
