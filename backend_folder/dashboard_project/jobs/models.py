from django.db import models


class JobMatchResult(models.Model):
    """
    Shared, global cache for job-match analyses -- deliberately has NO user
    foreign key, mirroring developers.Profile. Anyone who pastes the same
    job description against the same GitHub username hits this cached row
    instead of spending LLM tokens again, regardless of who they are.

    Per-user "I looked at this" tracking lives separately in
    common.models.SearchHistory, which points at rows here rather than
    duplicating them.
    """

    target_username = models.CharField(max_length=255)
    job_description_hash = models.CharField(max_length=64, db_index=True)
    job_description_text = models.TextField()
    match_result_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["target_username", "job_description_hash"])]

    def __str__(self):
        return f"{self.target_username} vs job {self.job_description_hash[:8]}"
