from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from openai import APIConnectionError, APITimeoutError, RateLimitError

from .models import Photo
from .services import analyze_image, embed_text, guess_mime_type

TRANSIENT_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError)


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_jitter=True)
def process_photo(self, photo_id: int) -> None:
    photo = Photo.objects.get(pk=photo_id)
    photo.status = Photo.Status.PROCESSING
    photo.error_message = ""
    photo.save(update_fields=["status", "error_message", "updated_at"])

    try:
        with photo.image.open("rb") as f:
            image_bytes = f.read()
        analysis = analyze_image(image_bytes, guess_mime_type(photo.image.name))
        description = analysis.description
        extracted_text = analysis.extracted_text

        embedding_input = description
        if extracted_text:
            embedding_input += f"\n\nText visible in the image: {extracted_text}"
        embedding = embed_text(embedding_input)
    except TRANSIENT_ERRORS as exc:
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            photo.status = Photo.Status.FAILED
            photo.error_message = f"Gave up after retries: {exc}"[:2000]
            photo.save(update_fields=["status", "error_message", "updated_at"])
            return
    except Exception as exc:
        photo.status = Photo.Status.FAILED
        photo.error_message = str(exc)[:2000]
        photo.save(update_fields=["status", "error_message", "updated_at"])
        return

    photo.description = description
    photo.extracted_text = extracted_text
    photo.embedding = embedding
    photo.status = Photo.Status.DONE
    photo.save(update_fields=["description", "extracted_text", "embedding", "status", "updated_at"])
