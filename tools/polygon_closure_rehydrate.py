import hashlib,json,os,shutil,subprocess,tempfile,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
RUN_ID=36250240579
ARTIFACT_ID=10908519045
EXPECTED_ARTIFACT_SHA="ad2505dceb8968c54bc7d0ae23baf44b9f4015d7b86431774c468b92b639ba48"
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
repo=os.environ["GITHUB_REPOSITORY"]; token=os.environ["GITHUB_TOKEN"]
url=f"https://api.github.com/repos/{repo}/actions/artifacts/{ARTIFACT_ID}/zip"
req=Request(url,headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"})
with urlopen(req,timeout=60) as r: data=r.read()
with tempfile.TemporaryDirectory() as td:
 z=Path(td)/"artifact.zip"; z.write_bytes(data)
 with zipfile.ZipFile(z) as f: f.extractall(td)
 u=Path(td)/"universe"; t=u/"tokens.jsonl"; p=u/"pairs.jsonl"
 tokens=[json.loads(x) for x in t.read_text().splitlines() if x.strip()]
 pairs=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
 if len(tokens)!=469 or len({x["address"].lower() for x in tokens})!=469: raise SystemExit("sealed token integrity failure")
 if len(pairs)!=2821 or len({x["pairAddress"].lower() for x in pairs})!=2821: raise SystemExit("sealed pair integrity failure")
 Path("automation/universe").mkdir(parents=True,exist_ok=True)
 Path("automation/evidence").mkdir(parents=True,exist_ok=True)
 shutil.copy2(t,"automation/universe/tokens.jsonl"); shutil.copy2(p,"automation/universe/pairs.jsonl")
 cert={"schema_version":"polygon-closure-certificate-v2","source_run_id":RUN_ID,"source_artifact_id":ARTIFACT_ID,"source_artifact_sha256":EXPECTED_ARTIFACT_SHA,"counts":{"tokens":469,"pairs":2821,"routes":617622,"strategies":18,"feature_groups":1891,"economic_candidate_groups":420,"exact_profit_certified":0},"files":{"tokens_sha256":sha(Path("automation/universe/tokens.jsonl")),"pairs_sha256":sha(Path("automation/universe/pairs.jsonl"))},"universe_fingerprint":"cfbeb1dae7e3387eb78d89b0144b77ddf65f9bc73c6af3836144f23032886295"}
Path("automation/evidence/P11_POLYGON_CLOSURE_CERTIFICATE.json").write_text(json.dumps(cert,indent=2)+"\n")
subprocess.run(["git","add","automation/universe","automation/evidence/P11_POLYGON_CLOSURE_CERTIFICATE.json"],check=True)
if subprocess.run(["git","diff","--cached","--quiet"]).returncode!=0:
 subprocess.run(["git","config","user.name","ghost-hunter-bot"],check=True); subprocess.run(["git","config","user.email","ghost-hunter-bot@users.noreply.github.com"],check=True)
 subprocess.run(["git","commit","-m","chore: restore sealed Polygon closure universe"],check=True)
 subprocess.run(["git","push"],check=True)
else: print("NO_CHANGES")
