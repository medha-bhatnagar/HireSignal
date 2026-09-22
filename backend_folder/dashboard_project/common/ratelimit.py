"""
Two-tier rate limiting, backed by the database (see RateLimitEntry in
common/models.py) rather than Redis, since no Redis is running yet.

The pattern is "fixed window": time is chopped into hour-long buckets, and
each key gets one counter per bucket. It's simpler than a sliding window and
good enough at this traffic scale -- the only real downside (a burst right
at the boundary between two windows could momentarily allow ~2x the limit)
doesn't matter much for protecting an LLM budget from casual abuse.

Two tiers:
  - Anonymous requests are keyed by a device id the extension generates on
    install (falls back to IP if the extension didn't send one), limited by
    RATE_LIMIT_ANONYMOUS_PER_HOUR.
  - Authenticated requests are keyed by user id, limited by
    RATE_LIMIT_AUTHENTICATED_PER_HOUR (higher, since logged-in users are
    using their own personal GitHub token/rate limit anyway -- see
    developers/services.py).
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from .models import RateLimitEntry


def _current_window_start():
    now = timezone.now()
    return now.replace(minute=0, second=0, microsecond=0)


def _rate_limit_key(request):
    """
    Returns (key, limit) for this request. request.user is set by the
    optional_jwt decorator in clients/decorators.py -- it runs BEFORE this,
    so by the time we get here we already know if this is an authenticated
    or anonymous caller.
    """
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return f"user:{user.id}", settings.RATE_LIMIT_AUTHENTICATED_PER_HOUR

    device_id = request.headers.get("X-Device-Id")
    identity = device_id or request.META.get("REMOTE_ADDR", "unknown")
    return f"anon:{identity}", settings.RATE_LIMIT_ANONYMOUS_PER_HOUR


def check_and_increment(request):
    """
    Atomically checks the current window's count against the limit and, if
    under it, increments it. Returns (allowed: bool, retry_after_seconds).

    The transaction + select_for_update prevents two near-simultaneous
    requests from both reading "9 out of 10" and both being allowed through,
    which a naive read-then-write would permit.
    """
    key, limit = _rate_limit_key(request)
    window_start = _current_window_start()

    with transaction.atomic():
        entry, _ = RateLimitEntry.objects.select_for_update().get_or_create(
            key=key, window_start=window_start, defaults={"request_count": 0}
        )
        if entry.request_count >= limit:
            retry_after = int(
                ((window_start + timedelta(hours=1)) - timezone.now()).total_seconds()
            )
            return False, max(retry_after, 1)

        entry.request_count += 1
        entry.save(update_fields=["request_count"])
        return True, 0


def rate_limited(view_func):
    """
    Decorator: enforces the rate limit before calling the view. Stack this
    AFTER optional_jwt (i.e. closer to the view) so request.user is already
    populated when this runs -- see developers/views.py for the order.
    """
    async def wrapper(request, *args, **kwargs):
        allowed, retry_after = await _check_async(request)
        if not allowed:
            response = JsonResponse(
                {"error": "Rate limit exceeded. Please slow down."}, status=429
            )
            response["Retry-After"] = str(retry_after)
            return response
        return await view_func(request, *args, **kwargs)

    return wrapper


async def _check_async(request):
    from asgiref.sync import sync_to_async

    return await sync_to_async(check_and_increment)(request)
