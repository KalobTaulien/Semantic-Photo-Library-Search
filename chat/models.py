from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Conversation(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Conversation({self.pk})"


class Message(TimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]

    @property
    def photos(self):
        """Plain Photo objects for this message's matches, in retrieval rank order."""
        return [mp.photo for mp in self.message_photos.all()]


class MessagePhoto(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_photos")
    photo = models.ForeignKey("photos.Photo", on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField()
    distance = models.FloatField(null=True)

    class Meta:
        ordering = ["rank"]
        constraints = [
            models.UniqueConstraint(fields=["message", "photo"], name="unique_message_photo"),
        ]
