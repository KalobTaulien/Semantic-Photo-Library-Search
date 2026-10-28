from django import forms
from django.conf import settings
from django.core.validators import FileExtensionValidator

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField that accepts and validates a list of files (Django docs' documented pattern)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class PhotoUploadForm(forms.Form):
    images = MultipleFileField(
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)],
    )

    def clean_images(self):
        files = self.cleaned_data["images"]
        for f in files:
            if f.size > settings.MAX_UPLOAD_SIZE:
                max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
                raise forms.ValidationError(f"{f.name} is larger than {max_mb}MB.")
        return files
