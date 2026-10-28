import uuid
from pathlib import Path


def user_photo_upload_path(instance, filename):
    """Store uploads under media/user_<id>/ so each user's library is isolated on disk."""
    ext = Path(filename).suffix.lower()
    return f"user_{instance.user_id}/{uuid.uuid4()}{ext}"
