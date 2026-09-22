from django.conf import settings
from django.db import models


class RateLimitEntry(models.Model):
    """
    A fixed-window request counter, used in place of Redis's INCR/EXPIRE
    pattern since there's no Redis running yet. One row per (key, window).

    `key` is either "user:<id>" for authenticated requests or
    "anon:<device_id_or_ip>" for anonymous ones -- see common/ratelimit.py.

    `window_start` is truncated to the top of the hour, so all requests
    within the same clock hour share one row and one counter. A new row
    is created automatically once the clock rolls into the next hour.
    """

    key = models.CharField(max_length=255)
    window_start = models.DateTimeField()
    request_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "window_start"], name="unique_ratelimit_window"
            )
        ]
        indexes = [models.Index(fields=["key", "window_start"])]

    def __str__(self):
        return f"{self.key} @ {self.window_start}: {self.request_count}"


class SearchHistory(models.Model):
    """
    A per-user pointer into the shared, global caches (developers.Profile,
    jobs.JobMatchResult) -- it does NOT duplicate the analysis itself, it
    just records that this user looked at this cached result, and when.

    This only ever gets a row written when request.user is set (i.e. the
    caller is authenticated) -- anonymous requests still benefit from the
    shared cache, they just don't get a history entry, since there's no
    identity to attach one to.
    """

    REQUEST_TYPES = [
        ("profile", "Profile analysis"),
        ("job_match", "Job match"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_history"
    )
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    target_username = models.CharField(max_length=255)

    # Only one of these two is set, depending on request_type.
    profile = models.ForeignKey(
        "developers.Profile", null=True, blank=True, on_delete=models.SET_NULL
    )
    job_match = models.ForeignKey(
        "jobs.JobMatchResult", null=True, blank=True, on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user} -> {self.request_type}:{self.target_username}"
