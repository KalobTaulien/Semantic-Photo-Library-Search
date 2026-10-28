from pgvector.django import CosineDistance

from photos.models import Photo
from photos.services import embed_text

TOP_K = 12
# Cosine distance cutoff (0 = identical direction, 1 = unrelated, 2 = opposite).
# Without this, a query always pulls back up to TOP_K photos regardless of how
# distant the "closest" ones actually are -- a narrow question would still drag
# in a dozen barely-related photos. This keeps responses scoped to genuine
# matches; broad queries that legitimately match many photos still return more,
# up to TOP_K, since they'll all fall under the threshold anyway.
MAX_DISTANCE = 0.6


def retrieve_photos(user, query: str):
    """Semantic search over a user's own described photos, nearest first, dropping anything too dissimilar to be a real match."""
    query_vector = embed_text(query)
    return (
        Photo.objects.filter(user=user, status=Photo.Status.DONE)
        .annotate(distance=CosineDistance("embedding", query_vector))
        .filter(distance__lt=MAX_DISTANCE)
        .order_by("distance")[:TOP_K]
    )
