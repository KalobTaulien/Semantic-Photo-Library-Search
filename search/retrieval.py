from pgvector.django import CosineDistance

from photos.models import Photo
from photos.services import embed_text

from .dates import extract_date_range, has_semantic_content

TOP_K = 12
# Cap for a pure date-browse query ("photos from last month") where there's no
# relevance ranking to narrow by -- higher than TOP_K since the point is to
# see everything from that period, not just the closest handful.
DATE_BROWSE_LIMIT = 60
# Cosine distance cutoff (0 = identical direction, 1 = unrelated, 2 = opposite).
# Without this, a query always pulls back up to TOP_K photos regardless of how
# distant the "closest" ones actually are -- a narrow question would still drag
# in a dozen barely-related photos. This keeps results scoped to genuine
# matches; broad queries that legitimately match many photos still return more,
# up to TOP_K, since they'll all fall under the threshold anyway.
MAX_DISTANCE = 0.65


def retrieve_photos(user, query: str):
    """Search a user's own described photos, optionally scoped by a date phrase in the query.

    A natural-language date phrase ("last month", "this week", "in March
    2025", "2024") is pulled out of the query first and applied as a
    created_at filter; whatever text is left is used for semantic search as
    before. If nothing meaningful is left after removing the date phrase and
    filler words (e.g. the whole query was just "photos from last month"),
    this skips semantic search entirely and returns everything from that
    period, newest first -- there's no content to rank by relevance.
    """
    date_range, remaining = extract_date_range(query)

    photos = Photo.objects.filter(user=user, status=Photo.Status.DONE)
    if date_range:
        start, end = date_range
        photos = photos.filter(created_at__gte=start, created_at__lt=end)

    if not has_semantic_content(remaining):
        return photos.order_by("-created_at")[:DATE_BROWSE_LIMIT]

    # Photo descriptions are always full descriptive sentences (how the vision
    # model writes them). A bare keyword query like "church" embeds much
    # further from its true match than a full sentence does, so it's wrapped
    # in a short descriptive frame to bring it into the same phrasing style as
    # the descriptions -- this measurably tightens the distance to genuine
    # matches without needing to loosen the threshold enough to let real
    # mismatches through.
    query_vector = embed_text(f"A photo of {remaining}.")
    return (
        photos.annotate(distance=CosineDistance("embedding", query_vector))
        .filter(distance__lt=MAX_DISTANCE)
        .order_by("distance")[:TOP_K]
    )
