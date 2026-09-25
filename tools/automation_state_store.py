#!/usr/bin/env python3
"""Restore the latest saturation conveyor state artifact, read-only except local file extraction."""
import argparse, io, json, os, sys, urllib.request, urllib.error, zipfile
from pathlib import Path

def api(path):
    token=os.environ.get('GITHUB_TOKEN')
    repo=os.environ.get('GITHUB_REPOSITORY','manish91082-coder/ghost-hunter-research-all-block-chains')
    req=urllib.request.Request('https://api.github.com'+path,headers={'Accept':'application/vnd.github+json','User-Agent':'ghost-hunter-state-store/1.0'})
    if token: req.add_header('Authorization',f'Bearer {token}')
    with urllib.request.urlopen(req,timeout=30) as r: return r.status,r.read(),r.headers

def restore(target):
    repo=os.environ.get('GITHUB_REPOSITORY','manish91082-coder/ghost-hunter-research-all-block-chains')
    try:
        status,raw,_=api(f'/repos/{repo}/actions/artifacts?name=saturation-conveyor-state&per_page=10')
        data=json.loads(raw); artifacts=[a for a in data.get('artifacts',[]) if not a.get('expired') and a.get('name')=='saturation-conveyor-state']
        artifacts.sort(key=lambda a:a.get('created_at',''),reverse=True)
        if not artifacts: print('NO_STATE_ARTIFACT'); return 0
        artifact=artifacts[0]
        _,zipraw,_=api(f'/repos/{repo}/actions/artifacts/{artifact["id"]}/zip')
        with zipfile.ZipFile(io.BytesIO(zipraw)) as z:
            names=z.namelist(); candidates=[n for n in names if n.endswith('saturation_state.json') or n.endswith('/saturation_state.json')]

            if not candidates: raise RuntimeError('state artifact missing saturation_state.json')
            Path(target).parent.mkdir(parents=True,exist_ok=True); Path(target).write_bytes(z.read(candidates[0]))
        print(f'RESTORED_ARTIFACT_ID={artifact["id"]}')
        return 0
    except urllib.error.HTTPError as e:
        print(f'ARTIFACT_API_HTTP_ERROR={e.code}',file=sys.stderr); return 0
    except Exception as e:
        print(f'ARTIFACT_RESTORE_ERROR={type(e).__name__}: {e}',file=sys.stderr); return 0

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('command',choices=['restore']); ap.add_argument('--target',default='automation/saturation_state.json'); args=ap.parse_args()
    raise SystemExit(restore(args.target))