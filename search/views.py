from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .retrieval import retrieve_photos


@login_required
def index(request):
    return render(request, "search/search.html")


@login_required
@require_http_methods(["POST"])
def query(request):
    search_query = request.POST.get("query", "").strip()
    if not search_query:
        return render(request, "search/_results.html", {})

    try:
        photos = list(retrieve_photos(request.user, search_query))
    except Exception:
        error = "Sorry, I couldn't search your photos just now. Check that OPENAI_API_KEY is set and try again."
        return render(request, "search/_results.html", {"error": error})

    return render(request, "search/_results.html", {"photos": photos, "searched": True})
