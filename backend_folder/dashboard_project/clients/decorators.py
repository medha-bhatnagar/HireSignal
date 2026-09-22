"""
optional_jwt: resolves *who* is calling, without ever blocking the request.

This is the piece that makes auth optional instead of a gate, per the
product decision made earlier: anonymous users can still use the extension
(shared rate limit, shared cache), while logged-in users get a higher
personal rate limit, their own GitHub token used for API calls, and a
SearchHistory trail. A view protected by this decorator should treat
request.user as "may or may not be set" and branch accordingly, rather than
assuming it's always present the way a normal @login_required view would.
"""
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def optional_jwt(view_func):
    async def wrapper(request, *args, **kwargs):
        request.user = None
        request.github_token = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ", 1)[1]
            try:
                token = AccessToken(raw_token)
                user = await sync_to_async(User.objects.get)(id=token["user_id"])
                request.user = user
                request.github_token = user.github_access_token or None
            except (TokenError, User.DoesNotExist):
                # Invalid/expired token: fall through as anonymous rather
                # than rejecting the request outright -- an expired token
                # shouldn't lock someone out of the anonymous tier.
                pass

        return await view_func(request, *args, **kwargs)

    return wrapper
