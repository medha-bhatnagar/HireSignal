import httpx
import os
import base64
from dotenv import load_dotenv
load_dotenv()

# Fallback token used for anonymous requests, or any call that doesn't pass
# a per-user token. Authenticated requests instead pass the calling user's
# own personal GitHub token (see accounts.models.User.github_access_token
# and developers/views.py), so their calls draw from their own 5,000/hr
# quota instead of this one shared pool.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"


def build_headers(token=None):
    """
    Builds the Authorization header for a GitHub API call. Pass the calling
    user's personal token when available; falls back to the shared
    GITHUB_TOKEN (the old, always-shared behavior) otherwise.
    """
    active_token = token or GITHUB_TOKEN
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {active_token}",
        "X-GitHub-Api-Version": "2026-03-10",
    }


async def request_user(username, token=None):
    url = f'{BASE_URL}/users/{username}'
    async with httpx.AsyncClient() as client:
        response = await client.get(
            #while waiting for GitHub to respond, Python
            #can work on other things
            url,
            headers=build_headers(token)
        )

        response.raise_for_status() #automatically raises exception if
                                    #an HTTP request fails
        return response.json()

async def request_repo(username, token=None):
    url = f'{BASE_URL}/users/{username}/repos'
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=build_headers(token)
        )
        response.raise_for_status()
        return response.json()

async def request_repo_info(username, repo, token=None):
    url = f'{BASE_URL}/repos/{username}/{repo}'
    async with httpx.AsyncClient() as client:
         response = await client.get(
              url,
              headers=build_headers(token)
         )
         response.raise_for_status()
         return response.json()

async def request_repo_languages(username, repo, token=None):
    url = f"{BASE_URL}/repos/{username}/{repo}/languages"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=build_headers(token)
        )
        response.raise_for_status()
        return response.json()


async def pull_info(username, repo, token=None):
    url =f'{BASE_URL}/repos/{username}/{repo}/pulls?state=all'
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=build_headers(token)
        )
        response.raise_for_status()
        data = response.json()
        print("Number of PRs returned:", len(data))
        return data

async def issues(username, repo, token=None):
    """Fetch all issues (excluding pull requests) for a repository."""

    url = f"{BASE_URL}/repos/{username}/{repo}/issues?state=all&per_page=100"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=build_headers(token))

        if response.status_code != 200:
            return []

        data = response.json()

        # Removing given pull requests
        return [
            issue
            for issue in data
            if "pull_request" not in issue
        ]


async def top_3_starred_repos(username, token=None):
    url = (
        f"https://api.github.com/search/repositories"
        f"?q=user:{username}&sort=stars&order=desc"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=build_headers(token))
        response.raise_for_status()

    items = response.json()["items"]

    top_repos = []

    # Add up to the first 3 repos
    for repo in items[:3]:
        top_repos.append({
            "name": repo["name"],
            "stars": repo["stargazers_count"]
        })

    # Fill remaining slots with None
    while len(top_repos) < 3:
        top_repos.append({
            "name": None,
            "stars": None
        })

    return top_repos

async def readme_encoded(username, repo, token=None):
    url = f"{BASE_URL}/repos/{username}/{repo}/readme"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=build_headers(token))
        if response.status_code == 404:
            return None
        response.raise_for_status()
    return response.json()

async def get_repo_contents(username, repo, path="", token=None):
    #List files/folders at a given path in a repo (default: root).
    url = f"{BASE_URL}/repos/{username}/{repo}/contents/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=build_headers(token))
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()


async def get_file_content(username, repo, path, token=None):
    """Fetch and decode a specific file's text content."""
    url = f"{BASE_URL}/repos/{username}/{repo}/contents/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=build_headers(token))
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

    encoded = data.get("content")
    if not encoded:
        return None
    return base64.b64decode(encoded).decode("utf-8", errors="ignore")
