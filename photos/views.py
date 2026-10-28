from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .forms import PhotoUploadForm
from .models import Photo
from .tasks import process_photo


@login_required
def library(request):
    photos = Photo.objects.filter(user=request.user)
    return render(request, "photos/library.html", {"photos": photos})


@login_required
@require_http_methods(["POST"])
def upload(request):
    form = PhotoUploadForm(request.POST, request.FILES)
    new_photos = []
    if form.is_valid():
        for image in form.cleaned_data["images"]:
            photo = Photo.objects.create(user=request.user, image=image)
            new_photos.append(photo)
            process_photo.delay(photo.pk)

    return render(
        request,
        "photos/_photo_cards.html",
        {"photos": new_photos, "errors": form.errors.get("images")},
    )


@login_required
def photo_status(request, pk):
    photo = get_object_or_404(Photo, pk=pk, user=request.user)
    return render(request, "photos/_photo_card.html", {"photo": photo})
