#!/usr/bin/env python3
"""Read-only GitHub Actions state extractor for Ghost Hunter research.

Usage:
  python tools/github_ci_state.py
  GITHUB_TOKEN=... python tools/github_ci_state.py

The script never writes to GitHub and never triggers or retries workflows.
It reports main HEAD, relevant workflow runs, jobs and artifacts.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "manish91082-coder"
REPO = "ghost-hunter-research-all-block-chains"
BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"
WORKFLOWS = [
    "polygon-readonly-verification",
    "polygon-p2-control-verification",
    "polygon-p2-derived-control-verification",
    "polygon-p2-control-function-verification",
]


def gh_get(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ghost-hunter-ci-state/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(BASE + path, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read())


def main():
    try:
        repo = gh_get("")
        branch = gh_get("/branches/main")
    except urllib.error.HTTPError as exc:
        print(f"GitHub API error: HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"GitHub API error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    head = branch["commit"]["sha"]
    report = {
        "repository": f"{OWNER}/{REPO}",
        "branch": "main",
        "head_sha": head,
        "default_branch": repo.get("default_branch"),
        "workflows": {},
    }

    for workflow_name in WORKFLOWS:
        try:
            data = gh_get(
                f"/actions/workflows/{workflow_name}.yml/runs"
                f"?branch=main&per_page=10"
            )
        except urllib.error.HTTPError:
            report["workflows"][workflow_name] = {"error": "workflow_not_found_or_unavailable"}
            continue

        runs = []
        for run in data.get("workflow_runs", []):
            run_row = {
                "id": run.get("id"),
                "run_number": run.get("run_number"),
                "head_sha": run.get("head_sha"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "created_at": run.get("created_at"),
                "updated_at": run.get("updated_at"),
                "html_url": run.get("html_url"),
            }
            try:
                jobs = gh_get(f"/actions/runs/{run['id']}/jobs?per_page=100")
                run_row["jobs"] = [
                    {
                        "id": job.get("id"),
                        "name": job.get("name"),
                        "status": job.get("status"),
                        "conclusion": job.get("conclusion"),
                    }
                    for job in jobs.get("jobs", [])
                ]
            except Exception as exc:
                run_row["jobs_error"] = f"{type(exc).__name__}: {exc}"

            try:
                artifacts = gh_get(f"/actions/runs/{run['id']}/artifacts?per_page=100")
                run_row["artifacts"] = [
                    {
                        "id": artifact.get("id"),
                        "name": artifact.get("name"),
                        "size_in_bytes": artifact.get("size_in_bytes"),
                        "expired": artifact.get("expired"),
                        "created_at": artifact.get("created_at"),
                        "digest": artifact.get("digest"),
                    }
                    for artifact in artifacts.get("artifacts", [])
                ]
            except Exception as exc:
                run_row["artifacts_error"] = f"{type(exc).__name__}: {exc}"

            runs.append(run_row)

        report["workflows"][workflow_name] = {
            "runs": runs,
            "latest_for_head": [
                run for run in runs if run.get("head_sha") == head
            ],
        }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
