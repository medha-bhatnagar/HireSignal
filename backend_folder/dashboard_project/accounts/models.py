from django.contrib.auth.models import AbstractUser
from django.db import models

from common.fields import EncryptedTextField


class User(AbstractUser):
    """
    Extends Django's built-in user with GitHub identity fields.

    github_id is what we key on (not github_username) because usernames can
    be changed by the user on GitHub's side, but the numeric id is stable
    for the lifetime of the account.

    github_access_token is the user's *personal* GitHub OAuth token. Storing
    it (encrypted) lets developers/services.py make GitHub API calls using
    the requesting user's own rate limit (5,000/hr) instead of one shared
    token across every user of the extension. It is never sent back to the
    extension -- only used server-side.
    """

    github_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    github_username = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    github_access_token = EncryptedTextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.github_username or self.username
