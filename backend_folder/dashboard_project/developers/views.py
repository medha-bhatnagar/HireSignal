from django.http import JsonResponse
from asgiref.sync import sync_to_async
from .models import Profile, MetricData, FileData
from ai.generate import generate_summary, generate_job_match
import json
from django.views.decorators.csrf import csrf_exempt

from clients.decorators import optional_jwt
from common.ratelimit import rate_limited
from common.models import SearchHistory
from cache.utils import get_or_set, make_cache_key
from jobs.models import JobMatchResult

from .services import(
    request_user,
    request_repo,
    request_repo_info,
    request_repo_languages,
    pull_info, 
    issues,
    top_3_starred_repos,
    readme_encoded,
    get_repo_contents,
    get_file_content
)
from .analytics import(
    profile_pic,
    creation_date,
    total_issues_opened,
    open_issues,
    closed_issues,
    issue_close_rate,
    top_languages,
    display_name,
    display_username,
    get_repo_name,
    get_bio,
    account_creation,
    top_languages,
    readme_decoded,
    profile_readme,
    is_recent,
    get_recent_repos,
    detect_repo_stack,
    detect_tech_stack
)


async def build_profile_data(username, token=None):
    # token: the requesting user's personal GitHub access token, if they're
    # logged in (set by clients.decorators.optional_jwt as
    # request.github_token). Threaded through every GitHub call below so an
    # authenticated user's lookups draw from their own 5,000/hr GitHub quota
    # instead of the shared fallback token in developers/services.py.
    bio = await get_bio(username, token=token) or ""
    name = await display_name(username, token=token) or ""
    pic = await profile_pic(username, token=token) or ""
    languages = await top_languages(username, token=token)
    stack = await detect_tech_stack(username, token=token)
    tech_stack = [lang["language"] for lang in languages if lang["language"]] + stack
    account_age = await account_creation(username, token=token)
    profile_text_readme = (await profile_readme(username, token=token) or "")[:4000]
    resolved_username = await display_username(username, token=token)

    return {
        "profile_image": pic,
        "full_name": name,
        "username": resolved_username,
        "profile_readme": profile_text_readme,
        "bio": bio,
        "account_age": account_age,
        "tech_stack": tech_stack,
    }


@optional_jwt
@rate_limited
async def analyze_profile(request, username):

    existing_profile = await sync_to_async(
        Profile.objects.filter(username=username).first
    )()

    if existing_profile and existing_profile.ai_summary:
        if request.user:
            await sync_to_async(SearchHistory.objects.create)(
                user=request.user,
                request_type="profile",
                target_username=existing_profile.username,
                profile=existing_profile,
            )
        return JsonResponse({
            "username": existing_profile.username,
            "full_name": existing_profile.full_name,
            "bio": existing_profile.bio,
            "tech_stack": existing_profile.tech_stack,
            "ai_summary": existing_profile.ai_summary,
            "saved": True,
        })

    save_profile = sync_to_async(Profile.objects.update_or_create)

    data = await build_profile_data(username, token=request.github_token)
    summary = await generate_summary(data)

    profile_obj, _ = await save_profile(
        username=data["username"],
        defaults={
            "profile_image": data["profile_image"],
            "full_name": data["full_name"],
            "username": data["username"],
            "profile_readme": data["profile_readme"],
            "bio": data["bio"],
            "account_age": data["account_age"],
            "tech_stack": data["tech_stack"],
            "ai_summary": summary,
        },
    )

    if request.user:
        await sync_to_async(SearchHistory.objects.create)(
            user=request.user,
            request_type="profile",
            target_username=data["username"],
            profile=profile_obj,
        )

    data["ai_summary"] = summary
    data["saved"] = True

    return JsonResponse(data)

@csrf_exempt
@optional_jwt
@rate_limited
async def match_job(request, username):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"},
            status=400
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )

    job_requirements = body.get("requirements", "")
    if not job_requirements:
        return JsonResponse(
            {"error": "Job requirements required"},
            status=400
        )

    job_hash = make_cache_key(username, job_requirements)

    # Get GitHub profile data (uses the caller's personal token if logged in)
    profile_data = await build_profile_data(username, token=request.github_token)

    # Hot cache (TTL'd, see cache/utils.py): avoids re-spending LLM tokens
    # for an identical username+job-description pair within the TTL window,
    # regardless of which user (or an anonymous caller) asks for it.
    async def compute_match():
        return await generate_job_match(profile_data, job_requirements)

    match = await get_or_set(f"job_match:{job_hash}", compute_match)

    # Durable record (never expires, unlike the cache above): this is what
    # SearchHistory points to, and what lets this result still be looked up
    # by an admin/analytics query even after the cache entry has expired.
    job_match_obj, _ = await sync_to_async(JobMatchResult.objects.update_or_create)(
        target_username=username,
        job_description_hash=job_hash,
        defaults={
            "job_description_text": job_requirements,
            "match_result_text": match,
        },
    )

    if request.user:
        await sync_to_async(SearchHistory.objects.create)(
            user=request.user,
            request_type="job_match",
            target_username=username,
            job_match=job_match_obj,
        )

    return JsonResponse({
        "username": username,
        "job_match": match
    })
    #get devs github data, send both dev data+job requirements 
    #to groq, return AI match
