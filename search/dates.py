import re
from datetime import datetime, timedelta

from django.utils import timezone

MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# Words that carry no real search intent once a date phrase is stripped out --
# e.g. "photos from last month" should reduce to "no semantic content", not
# search for the literal word "photos".
FILLER_WORDS = {
    "photo", "photos", "picture", "pictures", "pic", "pics", "image", "images",
    "show", "me", "my", "find", "get", "all", "of", "the", "a", "an", "any",
}

# Consumed as part of a date-phrase match so it's stripped along with the
# phrase itself, e.g. "from last month" -> "" not "from".
PREP = r"(?:from|in|during|since|for|on)\s+"

_MONTH_PATTERN = "|".join(sorted(MONTH_NAMES, key=len, reverse=True))


def _aware(d: datetime) -> datetime:
    return timezone.make_aware(d) if timezone.is_naive(d) else d


def _day_start(d) -> datetime:
    return _aware(datetime(d.year, d.month, d.day))


def _month_start(year: int, month: int) -> datetime:
    return _aware(datetime(year, month, 1))


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _week_start(d) -> datetime:
    monday = d - timedelta(days=d.weekday())
    return _day_start(monday)


def extract_date_range(query: str):
    """Find a natural-language date phrase in the query and return (date_range, remaining).

    date_range is a half-open (start, end) tz-aware datetime pair suitable for
    created_at__gte/__lt, or None if no date phrase was found. remaining is
    the query with the matched phrase (and its leading preposition, if any)
    removed, so semantic search can run on whatever content is left.
    """
    today = timezone.now().date()
    lowered = query.lower()

    def strip(match):
        remaining = lowered[: match.start()] + lowered[match.end() :]
        return re.sub(r"\s+", " ", remaining).strip()

    # Relative N-day/week/month windows, ending today (inclusive).
    m = re.search(rf"\b(?:{PREP})?(?:last|past)\s+(\d+)\s+days?\b", lowered)
    if m:
        n = int(m.group(1))
        start = _day_start(today - timedelta(days=n - 1))
        return (start, _day_start(today) + timedelta(days=1)), strip(m)

    m = re.search(rf"\b(?:{PREP})?(?:last|past)\s+(\d+)\s+weeks?\b", lowered)
    if m:
        n = int(m.group(1))
        start = _day_start(today - timedelta(weeks=n))
        return (start, _day_start(today) + timedelta(days=1)), strip(m)

    m = re.search(rf"\b(?:{PREP})?(?:last|past)\s+(\d+)\s+months?\b", lowered)
    if m:
        n = int(m.group(1))
        year, month = _add_months(today.year, today.month, -n)
        start = _month_start(year, month)
        return (start, _day_start(today) + timedelta(days=1)), strip(m)

    # Fixed calendar periods.
    m = re.search(rf"\b(?:{PREP})?today\b", lowered)
    if m:
        start = _day_start(today)
        return (start, start + timedelta(days=1)), strip(m)

    m = re.search(rf"\b(?:{PREP})?yesterday\b", lowered)
    if m:
        start = _day_start(today - timedelta(days=1))
        return (start, start + timedelta(days=1)), strip(m)

    m = re.search(rf"\b(?:{PREP})?this week\b", lowered)
    if m:
        start = _week_start(today)
        return (start, start + timedelta(days=7)), strip(m)

    m = re.search(rf"\b(?:{PREP})?last week\b", lowered)
    if m:
        start = _week_start(today) - timedelta(days=7)
        return (start, start + timedelta(days=7)), strip(m)

    m = re.search(rf"\b(?:{PREP})?this month\b", lowered)
    if m:
        start = _month_start(today.year, today.month)
        year, month = _add_months(today.year, today.month, 1)
        return (start, _month_start(year, month)), strip(m)

    m = re.search(rf"\b(?:{PREP})?last month\b", lowered)
    if m:
        year, month = _add_months(today.year, today.month, -1)
        start = _month_start(year, month)
        return (start, _month_start(today.year, today.month)), strip(m)

    m = re.search(rf"\b(?:{PREP})?this year\b", lowered)
    if m:
        start = _aware(datetime(today.year, 1, 1))
        return (start, _aware(datetime(today.year + 1, 1, 1))), strip(m)

    m = re.search(rf"\b(?:{PREP})?last year\b", lowered)
    if m:
        start = _aware(datetime(today.year - 1, 1, 1))
        return (start, _aware(datetime(today.year, 1, 1))), strip(m)

    # Month name, with or without an explicit year. Requires either a leading
    # preposition ("in march") or an attached year ("march 2025") -- a bare
    # month word floating in a sentence ("I may go") is too ambiguous
    # (especially "may") to treat as a date reference on its own.
    m = re.search(rf"\b{PREP}({_MONTH_PATTERN})\b(?:\s+(\d{{4}}))?", lowered)
    if not m:
        m = re.search(rf"\b({_MONTH_PATTERN})\s+(\d{{4}})\b", lowered)
    if m:
        month = MONTH_NAMES[m.group(1)]
        year = int(m.group(2)) if m.group(2) else today.year
        start = _month_start(year, month)
        next_year, next_month = _add_months(year, month, 1)
        return (start, _month_start(next_year, next_month)), strip(m)

    # Bare 4-digit year.
    m = re.search(rf"\b(?:{PREP})?((?:19|20)\d{{2}})\b", lowered)
    if m:
        year = int(m.group(1))
        return (_aware(datetime(year, 1, 1)), _aware(datetime(year + 1, 1, 1))), strip(m)

    return None, query


def has_semantic_content(text: str) -> bool:
    """Whether any non-filler words are left to actually search for."""
    words = set(re.findall(r"[a-z']+", text.lower()))
    return bool(words - FILLER_WORDS)
