"""
A thin cache-aside helper on top of Django's cache framework.

Cache-aside pattern: check the cache first; on a miss, compute the value,
store it, then return it. Callers don't need to know or care that the
backend is currently the database rather than Redis -- that's exactly the
point of going through Django's cache API instead of hand-rolling table
lookups per call site.

Used to cache generate_job_match() results in developers/views.py, keyed on
a hash of (username, job_description) so identical requests -- from the
same user or different users -- don't re-spend LLM tokens.
"""
import hashlib

from asgiref.sync import sync_to_async
from django.core.cache import cache

DEFAULT_TTL_SECONDS = 60 * 60 * 24  # 24 hours


def make_cache_key(*parts: str) -> str:
    """
    Builds a stable cache key from one or more strings by hashing their
    concatenation. Hashing (rather than just joining the strings) keeps keys
    a fixed, short length regardless of how long a pasted job description is,
    and avoids issues with special characters in raw text being used as a
    cache key directly.
    """
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


async def get_or_set(key: str, compute_fn, ttl: int = DEFAULT_TTL_SECONDS):
    """
    Async-friendly cache-aside: return the cached value for `key` if present;
    otherwise await compute_fn(), store the result, and return it.

    compute_fn must be an async callable taking no arguments (wrap with a
    lambda/partial at the call site if it needs arguments).
    """
    cached_value = await sync_to_async(cache.get)(key)
    if cached_value is not None:
        return cached_value

    value = await compute_fn()
    await sync_to_async(cache.set)(key, value, ttl)
    return value
