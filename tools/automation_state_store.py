#!/usr/bin/env python3
"""Restore the latest persistent saturation-conveyor working-set artifact."""
import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

def api(path):
    token=os.environ.get("GITHUB_TOKEN")
    repo=os.environ.get("GITHUB_REPOSITORY","manish91082-coder/ghost-hunter-research-all-block-chains")
    req=urllib.request.Request(
        "https://api.github.com"+path,
        headers={
            "Accept":"application/vnd.github+json",
            "User-Agent":"ghost-hunter-state-store/1.1",
        },
        method="GET",
    )
    if token:
        req.add_header("Authorization",f"Bearer {token}")
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status,r.read(),r.headers

def safe_member(name):
    p=Path(name)
    return not p.is_absolute() and ".." not in p.parts and name.startswith("automation/")

def restore(target):
    repo=os.environ.get("GITHUB_REPOSITORY","manish91082-coder/ghost-hunter-research-all-block-chains")
    try:
        _,raw,_=api(f"/repos/{repo}/actions/artifacts?name=saturation-conveyor-state&per_page=20")
        data=json.loads(raw)
        artifacts=[
            a for a in data.get("artifacts",[])
            if not a.get("expired") and a.get("name")=="saturation-conveyor-state"
        ]
        artifacts.sort(key=lambda a:a.get("created_at",""),reverse=True)
        if not artifacts:
            print("NO_STATE_ARTIFACT")
            return 0

        artifact=artifacts[0]
        _,zipraw,_=api(f"/repos/{repo}/actions/artifacts/{artifact['id']}/zip")
        with zipfile.ZipFile(io.BytesIO(zipraw)) as z:
            members=[n for n in z.namelist() if not n.endswith("/") and safe_member(n)]
            if not any(n.endswith("automation/saturation_state.json") or n=="automation/saturation_state.json" for n in members):
                raise RuntimeError("persistent artifact missing automation/saturation_state.json")

            for name in members:
                destination=Path(name)
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(z.read(name))

        # Make the explicit target check part of the contract.
        if not Path(target).exists():
            raise RuntimeError(f"restored checkpoint missing: {target}")
        print(f"RESTORED_ARTIFACT_ID={artifact['id']}")
        print(f"RESTORED_FILES={len(members)}")
        return 0

    except urllib.error.HTTPError as e:
        print(f"ARTIFACT_API_HTTP_ERROR={e.code}",file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ARTIFACT_RESTORE_ERROR={type(e).__name__}: {e}",file=sys.stderr)
        return 2

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["restore"])
    ap.add_argument("--target",default="automation/saturation_state.json")
    args=ap.parse_args()
    raise SystemExit(restore(args.target))
