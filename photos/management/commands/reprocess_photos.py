from django.core.management.base import BaseCommand

from photos.models import Photo
from photos.tasks import process_photo


class Command(BaseCommand):
    help = "Re-run captioning/text-extraction/embedding for existing photos (e.g. after a prompt or schema change)."

    def add_arguments(self, parser):
        parser.add_argument("--photo-id", type=int, help="Reprocess a single photo by id.")

    def handle(self, *args, **options):
        photos = Photo.objects.all()
        photo_id = options.get("photo_id")
        if photo_id:
            photos = photos.filter(pk=photo_id)

        count = 0
        for photo in photos:
            process_photo.delay(photo.pk)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Queued {count} photo(s) for reprocessing."))
