import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Type

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

GITHUB_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
PLACEHOLDER_TOKENS = {"", "your-github-personal-access-token", "ghp_your-token", "your-token"}


def normalize_github_repository(value: str) -> str:
    normalized = value.strip().rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/", "www.github.com/"):
        if normalized.lower().startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    parts = [part for part in normalized.split("/") if part]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return normalized


def github_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token and token not in PLACEHOLDER_TOKENS and not token.startswith("your-"):
        headers["Authorization"] = f"Bearer {token}"
    return headers


def validate_github_repository(repository: str) -> Dict[str, Any]:
    normalized = normalize_github_repository(repository)
    if not normalized:
        return {"valid": False, "error": "GitHub repository is required in owner/repo format"}
    if not GITHUB_REPO_PATTERN.match(normalized):
        return {"valid": False, "error": "Repository must use owner/repo format"}

    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(
                f"https://api.github.com/repos/{normalized}",
                headers=github_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "repository": normalized,
                    "full_name": data.get("full_name"),
                    "default_branch": data.get("default_branch"),
                    "html_url": data.get("html_url"),
                }
            if response.status_code == 404:
                return {"valid": False, "error": f"Repository '{normalized}' was not found"}
            if response.status_code == 403:
                return {"valid": False, "error": "GitHub access denied. Add GITHUB_TOKEN for private repositories"}
            return {"valid": False, "error": f"GitHub API returned status {response.status_code}"}
    except httpx.RequestError as exc:
        return {"valid": False, "error": f"Could not reach GitHub: {exc}"}


class GitHubDeploymentInput(BaseModel):
    repository: str = Field(..., description="GitHub repository in owner/repo format")
    service_name: str = Field(default="", description="Affected service name")
    hours_back: int = Field(default=24, description="Lookback window in hours")


class GitHubDeploymentTool(BaseTool):
    name: str = "github_deployments"
    description: str = (
        "Reads recent commits, deployments, merged pull requests, and workflow runs "
        "from a real GitHub repository."
    )
    args_schema: Type[BaseModel] = GitHubDeploymentInput

    def _run(self, repository: str, service_name: str = "", hours_back: int = 24) -> str:
        normalized = normalize_github_repository(repository)
        validation = validate_github_repository(normalized)
        if not validation["valid"]:
            return json.dumps({"error": validation["error"], "repository": normalized}, indent=2)
        return self._fetch_repository_activity(normalized, service_name, hours_back, validation)

    def _fetch_repository_activity(self, repository: str, service_name: str, hours_back: int, repo_meta: dict) -> str:
        since = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"
        headers = github_headers()

        try:
            with httpx.Client(timeout=30) as client:
                commits_resp = client.get(
                    f"https://api.github.com/repos/{repository}/commits",
                    headers=headers,
                    params={"since": since, "per_page": 20},
                )
                deploys_resp = client.get(
                    f"https://api.github.com/repos/{repository}/deployments",
                    headers=headers,
                    params={"per_page": 10},
                )
                pulls_resp = client.get(
                    f"https://api.github.com/repos/{repository}/pulls",
                    headers=headers,
                    params={"state": "closed", "sort": "updated", "direction": "desc", "per_page": 10},
                )
                workflows_resp = client.get(
                    f"https://api.github.com/repos/{repository}/actions/runs",
                    headers=headers,
                    params={"per_page": 10},
                )

                commits = commits_resp.json() if commits_resp.status_code == 200 else []
                deployments = deploys_resp.json() if deploys_resp.status_code == 200 else []
                pulls = pulls_resp.json() if pulls_resp.status_code == 200 else []
                workflow_payload = workflows_resp.json() if workflows_resp.status_code == 200 else {}
                workflow_runs = workflow_payload.get("workflow_runs", []) if isinstance(workflow_payload, dict) else []

                payload = {
                    "source": "github_deployments",
                    "repository": repository,
                    "repository_url": repo_meta.get("html_url"),
                    "service": service_name,
                    "hours_back": hours_back,
                    "recent_commits": [
                        {
                            "sha": item.get("sha", "")[:7],
                            "message": item.get("commit", {}).get("message", ""),
                            "author": item.get("commit", {}).get("author", {}).get("name", ""),
                            "date": item.get("commit", {}).get("author", {}).get("date", ""),
                            "url": item.get("html_url", ""),
                        }
                        for item in commits[:10]
                    ],
                    "recent_deployments": [
                        {
                            "id": item.get("id"),
                            "environment": item.get("environment"),
                            "description": item.get("description"),
                            "created_at": item.get("created_at"),
                            "sha": item.get("sha", "")[:7] if item.get("sha") else None,
                        }
                        for item in deployments[:10]
                    ],
                    "recent_merged_prs": [
                        {
                            "number": item.get("number"),
                            "title": item.get("title"),
                            "merged_at": item.get("merged_at"),
                            "user": item.get("user", {}).get("login", ""),
                            "url": item.get("html_url", ""),
                        }
                        for item in pulls[:5]
                        if item.get("merged_at")
                    ],
                    "recent_workflow_runs": [
                        {
                            "name": item.get("name"),
                            "status": item.get("status"),
                            "conclusion": item.get("conclusion"),
                            "created_at": item.get("created_at"),
                            "head_branch": item.get("head_branch"),
                            "html_url": item.get("html_url"),
                        }
                        for item in workflow_runs[:10]
                    ],
                }
                return json.dumps(payload, indent=2, default=str)
        except Exception as exc:
            return json.dumps({"error": f"GitHub request failed: {exc}", "repository": repository}, indent=2)
