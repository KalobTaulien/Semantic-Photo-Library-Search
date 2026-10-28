from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField

from common.models import TimeStampedModel

from .storage import user_photo_upload_path


class Photo(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=user_photo_upload_path)
    description = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True, default="")
    embedding = VectorField(dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            HnswIndex(
                name="photo_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Photo({self.pk}) user={self.user_id} status={self.status}"
