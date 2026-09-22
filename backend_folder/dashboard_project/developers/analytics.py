from .services import request_user,get_repo_contents,get_file_content, readme_encoded, request_repo, request_repo_info, request_repo_languages, pull_info, issues 
from collections import defaultdict
import base64
from datetime import datetime, timedelta, timezone

INFRA_INDICATORS = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".github": "GitHub Actions (CI/CD)",  
    "Jenkinsfile": "Jenkins",
    "terraform": "Terraform",             
    ".gitlab-ci.yml": "GitLab CI",
    "vercel.json": "Vercel",
    "netlify.toml": "Netlify",
}

DEPENDENCY_FILES = {
    "package.json": "npm",
    "requirements.txt": "pip",
    "Pipfile": "pipenv",
    "pyproject.toml": "poetry/pip",
    "Cargo.toml": "cargo",
    "go.mod": "go modules",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "Gemfile": "bundler",
}

FRAMEWORK_KEYWORDS = {
    "react": "React", "next": "Next.js", "vue": "Vue.js", "express": "Express",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "spring-boot": "Spring Boot", "rails": "Ruby on Rails",
    "tensorflow": "TensorFlow", "torch": "PyTorch", "pandas": "Pandas",
    "psycopg2": "PostgreSQL", "pymongo": "MongoDB", "mongoose": "MongoDB",
    "redis": "Redis", "sqlalchemy": "SQLAlchemy", "mysql": "MySQL",
}

# NOTE: every function below now takes an optional `token` kwarg, threaded
# straight through to the services.py call(s) it makes. Pass the requesting
# user's personal GitHub token (from request.github_token, set by
# clients.decorators.optional_jwt) so authenticated calls use that user's
# own rate limit instead of the shared GITHUB_TOKEN fallback.

async def merged_percentage(username, repo, token=None):
    info = await pull_info(username, repo, token=token)
    if not info:
        return "N/A"
    total_prs = len(info)
    merged_prs = sum(
        1 for pr in info
        if pr["merged_at"] is not None
    )
#print(merged_percentage('python', 'cpython')) 

async def profile_pic(username, token=None):
    info = await request_user(username, token=token)
    if info:
        profile_url = info.get("html_url") + ".png"
    return profile_url

async def forks(username, repo, token=None):# NOT SURE ABOUT USE
    info = await request_repo_info(username, repo, token=token)
    return info.get('forks')

async def creation_date(username, repo, token=None):
    info = await request_repo_info(username, repo, token=token)
    return info.get('created_at')
    #coordinated universal time, may have to convert to date time
async def stars(username, repo, token=None):
    info = await request_repo_info(username, repo, token=token)
    return info.get('stargazers_count')

async def last_updated(username, repo, token=None): # NOT SURE ABOUT USE
    info = await request_repo_info(username, repo, token=token)
    return info.get('updated_at')
    #coordinated universal time, may have to convert to date time

async def total_issues_opened(username, repo, token=None):
    issue_data = await issues(username, repo, token=token)
    return len(issue_data)


async def open_issues(username, repo, token=None):
    issue_data = await issues(username, repo, token=token)
    return sum(
        1
        for issue in issue_data
        if issue["state"] == "open"
    )


async def closed_issues(username, repo, token=None):
    issue_data = await issues(username, repo, token=token)
    return sum(
        1
        for issue in issue_data
        if issue["state"] == "closed"
    )

async def issue_close_rate(username, repo, token=None):
    issue_data = await issues(username, repo, token=token)
    total = len(issue_data)
    if total == 0:
        return 0
    closed = sum(
        1
        for issue in issue_data
        if issue["state"] == "closed"
    )
    term = f'{int((closed/total) * 100)}%'
    return term

async def display_name(username, token=None):
    info = await request_user(username, token=token)
    return info.get("name")

async def display_username(username, token=None):
    info = await request_user(username, token=token)
    return info.get("login")

async def get_repo_name(username, token=None):
    repo_list = []
    repos = await request_repo(username, token=token)
    for repo in repos:
            repo_list.append(repo['name'])
    return repo_list

async def get_bio(username, token=None):
    info = await request_user(username, token=token)
    return info.get("bio")

async def account_creation(username, token=None):
    info = await request_user(username, token=token)
    account_age = info.get("created_at")
    if account_age:
        account_age = datetime.fromisoformat(
        account_age.replace("Z", "+00:00"))
    return account_age

async def top_languages(username, token=None):
    repos = await request_repo(username, token=token)

    language_totals = defaultdict(int)

    # Sum bytes for each language across all repositories
    for repo in repos:
        repo_languages = await request_repo_languages(
            username,
            repo["name"],
            token=token
        )

        for language, bytes_of_code in repo_languages.items():
            language_totals[language] += bytes_of_code

    total_bytes = sum(language_totals.values())

    if total_bytes == 0:
        return [
            {"language": None, "percentage": None},
            {"language": None, "percentage": None},
            {"language": None, "percentage": None},
        ]

    sorted_languages = sorted(
        language_totals.items(),
        key=lambda item: item[1],
        reverse=True
    )

    top_three = []

    for language, bytes_of_code in sorted_languages[:3]:
        percentage = round((bytes_of_code / total_bytes) * 100)

        if percentage == 0:
            percentage = "<1"

        top_three.append({
            "language": language,
            "percentage": f"{percentage}%"
            if percentage != "<1"
            else "<1%"
        })

    while len(top_three) < 3:
        top_three.append({
            "language": None,
            "percentage": None
        })

    return top_three

async def readme_decoded(username, repo, token=None):
    data = await readme_encoded(username, repo, token=token)
    if data is None:
        return None
    encoded = data.get("content")
    text = base64.b64decode(encoded).decode("utf-8")
    return text

async def profile_readme(username, token=None):
    text = await readme_decoded(username, username, token=token)
    if text is None:
        return None
    return text


def is_recent(repo, months=18):
    #Check if a repo has been pushed to within the last N months.
    pushed_at = repo.get("pushed_at")
    if not pushed_at:
        return False
    pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    return pushed_date > cutoff


async def get_recent_repos(username, months=18, token=None):
    repos = await request_repo(username, token=token)
    return [r for r in repos if is_recent(r, months)]

async def detect_repo_stack(username, repo_name, token=None):
    #Detect infra + framework signals for a single repo.
    detected = set()

    contents = await get_repo_contents(username, repo_name, token=token)
    filenames = {item["name"] for item in contents if item["type"] == "file"}
    folder_names = {item["name"] for item in contents if item["type"] == "dir"}

    # infra detection — direct filename match
    for filename, label in INFRA_INDICATORS.items():
        if filename in filenames or filename in folder_names:
            detected.add(label)

    # dependency file detection + parse contents for framework keywords
    for filename in DEPENDENCY_FILES:
        if filename in filenames:
            content = await get_file_content(username, repo_name, filename, token=token)
            if content:
                content_lower = content.lower()
                for keyword, label in FRAMEWORK_KEYWORDS.items():
                    if keyword in content_lower:
                        detected.add(label)

    return detected

async def detect_tech_stack(username, months=18, token=None):
    #Aggregate tech stack across a user's recently active repos
    recent_repos = await get_recent_repos(username, months, token=token)

    full_stack = set()
    for repo in recent_repos:
        repo_stack = await detect_repo_stack(username, repo["name"], token=token)
        full_stack.update(repo_stack)

    return list(full_stack)
