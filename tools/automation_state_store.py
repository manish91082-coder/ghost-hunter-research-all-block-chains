#!/usr/bin/env python3
"""Restore the latest persistent saturation-conveyor artifact via GitHub CLI."""
import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

DEFAULT_REPO = "manish91082-coder/ghost-hunter-research-all-block-chains"
ARTIFACT = "saturation-conveyor-state"

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=90)

def safe_member(path: Path) -> bool:
    return not path.is_absolute() and ".." not in path.parts

def latest_completed_run(repo: str):
    import json
    completed = []
    for workflow in ("saturation-conveyor.yml", "p4-rpc-fanout.yml"):
        cmd = [
            "gh", "run", "list",
            "--repo", repo,
            "--workflow", workflow,
            "--limit", "30",
            "--json", "databaseId,status,conclusion,createdAt",
        ]
        p = run(cmd)
        if p.returncode != 0:
            raise RuntimeError(f"gh run list failed for {workflow}: {p.stderr.strip()}")
        rows = json.loads(p.stdout or "[]")
        completed.extend(r for r in rows if r.get("status") == "completed")
    completed.sort(key=lambda r: r.get("createdAt", ""), reverse=True)
    return completed[0] if completed else None

def restore(target: str):
    repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO)
    target_path = Path(target)
    with tempfile.TemporaryDirectory(prefix="conveyor-artifact-") as tmp:
        tmp_path = Path(tmp)
        latest = latest_completed_run(repo)
        if latest is None:
            print("NO_COMPLETED_RUN")
            return 0

        cmd = [
            "gh", "run", "download", str(latest["databaseId"]),
            "--repo", repo,
            "--name", ARTIFACT,
            "--dir", str(tmp_path),
        ]
        p = run(cmd)
        if p.returncode != 0:
            raise RuntimeError(f"gh run download failed: {p.stderr.strip()}")

        files = [p for p in tmp_path.rglob("*") if p.is_file()]
        if not files:
            raise RuntimeError("downloaded artifact is empty")

        # The artifact is created from automation/* and therefore restores only
        # the automation working set. Reject any unexpected archive traversal.
        for src in files:
            rel = src.relative_to(tmp_path)
            if not safe_member(rel):
                raise RuntimeError(f"unsafe artifact member: {rel}")

        target_root = target_path.parent
        target_root.mkdir(parents=True, exist_ok=True)

        for src in files:
            rel = src.relative_to(tmp_path)
            dest = target_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    if not target_path.exists():
        raise RuntimeError(f"restored checkpoint missing: {target_path}")

    print(f"RESTORED_RUN_ID={latest['databaseId']}")
    print("RESTORED_FILES=working-set")
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["restore"])
    ap.add_argument("--target", default="automation/saturation_state.json")
    args = ap.parse_args()
    raise SystemExit(restore(args.target))
