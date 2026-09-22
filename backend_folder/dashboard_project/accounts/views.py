"""
The GitHub OAuth code-exchange, hand-rolled (no allauth/social-auth).

Flow recap (see the extension's background.js for the other half):
  1. Extension opens GitHub's authorize page via chrome.identity.
  2. GitHub redirects back to the extension with a one-time `code`.
  3. Extension POSTs that code here.
  4. We trade the code + our client secret for a GitHub access token.
  5. We use that token, once, to fetch the user's GitHub identity.
  6. We create/update our own User row and store their personal GitHub
     token (encrypted) for future per-user API calls.
  7. We mint our OWN JWT pair and return that -- the GitHub token itself is
     never sent back to the extension.
"""
import json

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@csrf_exempt
@require_POST
async def github_callback(request):
    try:
        code = json.loads(request.body).get("code")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not code:
        return JsonResponse({"error": "Missing code"}, status=400)

    async with httpx.AsyncClient(timeout=10) as client:
        token_res = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if token_res.status_code != 200:
            return JsonResponse({"error": "GitHub token exchange failed"}, status=502)

        github_token = token_res.json().get("access_token")
        if not github_token:
            return JsonResponse(
                {"error": "No access token returned by GitHub"}, status=400
            )

        user_res = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {github_token}"},
        )
        if user_res.status_code != 200:
            return JsonResponse({"error": "Failed to fetch GitHub identity"}, status=502)
        gh_user = user_res.json()

    user, _ = await sync_to_async(User.objects.update_or_create)(
        github_id=str(gh_user["id"]),
        defaults={
            "username": gh_user["login"],
            "github_username": gh_user["login"],
            "avatar_url": gh_user.get("avatar_url", ""),
            # Stored (encrypted, see common/fields.py) so future GitHub API
            # calls made on this user's behalf use their own rate limit
            # instead of the shared GITHUB_TOKEN in developers/services.py.
            "github_access_token": github_token,
        },
    )

    refresh = RefreshToken.for_user(user)
    return JsonResponse(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user.github_username,
        }
    )


@csrf_exempt
@require_POST
async def refresh_token(request):
    try:
        refresh_str = json.loads(request.body).get("refresh")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not refresh_str:
        return JsonResponse({"error": "Missing refresh token"}, status=400)

    try:
        refresh = RefreshToken(refresh_str)
        new_access = str(refresh.access_token)
    except TokenError:
        return JsonResponse({"error": "Invalid or expired refresh token"}, status=401)

    return JsonResponse({"access": new_access})
