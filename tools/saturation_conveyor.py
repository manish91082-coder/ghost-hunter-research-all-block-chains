#!/usr/bin/env python3
"""Manifest-driven autonomous evidence conveyor for Polygon P2-P11.
Runs bounded work, checkpoints state, preserves failures, and never promotes
a research gate from a single failed/partial observation.
"""
import argparse, hashlib, json, os, subprocess, sys, time, shutil
from pathlib import Path

STATE=Path('automation/saturation_state.json')
PLAN=Path('automation/saturation_plan.json')
EVID=Path('automation/evidence')
REPORT=Path('automation/conveyor_report.json')

CRITICAL_P2=['P2_REGRESSION','P2_DERIVED','P2_CONTROL_FUNCTION','P2_PROVENANCE']
PROMOTION=['P3','P4','P5','P6','P7','P8','P9','P10','P11']
SHADOW=['P3','P4','P5','P6','P7','P8','P9','P10']
WORKER=Path('tools/polygon_universe_worker.py')
CODE_EPOCH_FILES=[
    Path("tools/saturation_conveyor.py"),
    Path("tools/polygon_universe_worker.py"),
    Path("tools/automation_state_store.py"),
    Path("chains/polygon-pos/polygon_p2_control_function_verifier.py"),
    Path("chains/polygon-pos/polygon_p2_control_function_reconciliation.py"),
    Path("chains/polygon-pos/polygon_readonly_verifier.py"),
    Path("chains/polygon-pos/p2_control_function_targets.txt"),
    Path("chains/polygon-pos/p2_derived_control_targets.txt"),
    Path("chains/polygon-pos/p4_seed_tokens.txt"),
]

def current_code_epoch():
    h=hashlib.sha256()
    for path in CODE_EPOCH_FILES:
        if path.exists():
            h.update(str(path).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


TASK_REVISIONS={"P3":"p3-multisource-closure-v1","P4":"p4-parallel-endpoint-discovery-v3","P5":"p5-full-universe-v1"}

def now(): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def load_json(p,default):
    p=Path(p)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def save_json(p,v):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def run(cmd, timeout=600):
    started=time.time()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
        return {'ok':p.returncode==0,'returncode':p.returncode,'elapsed_sec':round(time.time()-started,2),'stdout':p.stdout[-12000:],'stderr':p.stderr[-12000:]}
    except subprocess.TimeoutExpired as e:
        return {'ok':False,'returncode':124,'elapsed_sec':round(time.time()-started,2),'stdout':(e.stdout or '')[-12000:],'stderr':(e.stderr or '')[-12000:],'timeout':True}
    except Exception as e:
        return {'ok':False,'returncode':125,'elapsed_sec':round(time.time()-started,2),'error':f'{type(e).__name__}: {e}'}

def run_p2_derived():
    cmd=['python','chains/polygon-pos/polygon_readonly_verifier.py','--rpc-pool-file','chains/polygon-pos/rpc_pool.txt','--min-request-interval','1.0','--min-head-endpoints','2','--min-code-endpoints','2','--code-recovery-rounds','2','--stale-block-tolerance','2','--address','@chains/polygon-pos/p2_derived_control_targets.txt']
    a=run(cmd,timeout=700)
    b=run(['python','chains/polygon-pos/polygon_p2_derived_reconciliation.py'],timeout=60)
    recon=load_json(Path('polygon_p2_derived_reconciliation.json'),{})
    return {'ok':a['ok'] and b['ok'],'verifier':a,'reconciliation':b,'reconciliation_state':recon.get('evidence_state')}

def run_p2_control():
    cmd=['python','chains/polygon-pos/polygon_p2_control_function_verifier.py','--rpc-pool-file','chains/polygon-pos/rpc_pool.txt','--min-request-interval','1.0','--min-head-endpoints','2','--head-recovery-rounds','3','--min-probe-endpoints','2','--recovery-rounds','2','--stale-block-tolerance','2','--target-file','chains/polygon-pos/p2_control_function_targets.txt']
    a=run(cmd,timeout=800)
    obs_path=Path('polygon_p2_control_function_observations.jsonl')
    if a['ok'] and obs_path.exists():
        b=run(['python','chains/polygon-pos/polygon_p2_control_function_reconciliation.py'],timeout=60)
    else:
        b={'ok':False,'returncode':125,'elapsed_sec':0,'stdout':'','stderr':'Reconciliation skipped because live verifier did not produce a valid observation set'}
    recon=load_json(Path('polygon_p2_control_function_reconciliation.json'),{})
    return {'ok':a['ok'] and b['ok'],'verifier':a,'reconciliation':b,'reconciliation_state':recon.get('evidence_state')}

def copy_summary(src,name):
    p=Path(src)
    if p.exists():
        EVID.mkdir(parents=True,exist_ok=True); shutil.copy2(p,EVID/name)
def normalize_task_result(task,result):
    return {'task':task,'time':now(),'ok':bool(result.get('ok')),'result':result}

def execute(task):
    if task=='P2_REGRESSION':
        return run(['python','chains/polygon-pos/test_p2_control_function_regression.py'],timeout=120)
    if task=='P2_DERIVED':
        r=run_p2_derived(); copy_summary('polygon_p2_derived_reconciliation.json','P2_DERIVED_LATEST.json'); return r
    if task=='P2_CONTROL_FUNCTION':
        r=run_p2_control(); copy_summary('polygon_p2_control_function_reconciliation.json','P2_CONTROL_FUNCTION_LATEST.json'); return r
    if task=='P2_PROVENANCE':
        r=run(['python',str(WORKER),'--task','P2_PROVENANCE'],timeout=700); copy_summary('automation/evidence/P2_PROVENANCE_REPLAY.json','P2_PROVENANCE_LATEST.json'); return r
    return run(['python',str(WORKER),'--task',task],timeout=500)

def task_state(state,task):
    return state['tasks'].setdefault(task,{'attempts':0,'ok':False,'last_error':'','last_run':None,'cooldown_until':0})


def critical_task_complete(task, state):
    """Skip already-closed critical work and avoid redoing proven evidence every heartbeat."""
    if task == 'P2_REGRESSION':
        ts=state.get('tasks',{}).get(task,{})
        return bool(ts.get('ok')) and ts.get('code_epoch') == current_code_epoch()
    if task == 'P2_DERIVED':
        p=Path('automation/evidence/P2_DERIVED_LATEST.json')
        return p.exists() and load_json(p,{}).get('evidence_state') == 'VERIFIED'
    if task == 'P2_CONTROL_FUNCTION':
        p=Path('automation/evidence/P2_CONTROL_FUNCTION_LATEST.json')
        return p.exists() and load_json(p,{}).get('evidence_state') == 'VERIFIED'
    if task == 'P2_PROVENANCE':
        p=Path('automation/evidence/P2_PROVENANCE_LATEST.json')
        return p.exists() and load_json(p,{}).get('status') == 'REPLAYED'
    return False

def stage_ready(stage):
    files={
      'P3':Path('automation/evidence/P3_PROTOCOL_SNAPSHOT.json'),
      'P4':Path('automation/evidence/P4_TOKEN_SNAPSHOT.json'),
      'P5':Path('automation/evidence/P5_PAIR_SNAPSHOT.json'),
      'P6':Path('automation/evidence/P6_ROUTE_SNAPSHOT.json'),
      'P7':Path('automation/evidence/P7_STRATEGY_MATRIX.json'),
      'P8':Path('automation/evidence/P8_FEATURE_SNAPSHOT.json'),
      'P9':Path('automation/evidence/P9_ECONOMIC_SCREEN.json'),
      'P10':Path('automation/evidence/P10_SATURATION_AUDIT.json'),
      'P11':Path('automation/evidence/P11_CLOSURE_REPORT.json'),
    }
    p=files.get(stage)
    if p is None or not p.exists(): return False
    try:
        data=json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return False
    # A first-pass snapshot is preparation evidence, not saturation completion.
    # Promotion requires an explicit stage_gate=CLOSED marker produced by a
    # stage-specific closure worker. P11 additionally requires READY.
    if stage in {'P3','P4','P5','P6','P7','P8','P9','P10'}:
        return data.get('stage_gate') == 'CLOSED'
    if stage=='P11':
        return data.get('status')=='READY'
    return False

def shadow_dependency_override(task):
    # Always fill the earliest missing shadow prerequisite first. This keeps the
    # conveyor productive when an upstream queue is empty or a downstream
    # snapshot was created from an empty source.
    checks=[
        ("P3", Path("automation/evidence/P3_PROTOCOL_SNAPSHOT.json").exists()),
        ("P4", Path("automation/universe/tokens.jsonl").exists() and bool(Path("automation/universe/tokens.jsonl").read_text(encoding="utf-8").strip())),
        ("P5", Path("automation/universe/pairs.jsonl").exists() and bool(Path("automation/universe/pairs.jsonl").read_text(encoding="utf-8").strip())),
    ]
    if not checks[0][1]:
        return "P3"
    if not checks[1][1]:
        return "P4"
    if not checks[2][1]:
        return "P5"

    p6=Path("automation/evidence/P6_ROUTE_SNAPSHOT.json")
    if not p6.exists():
        return "P6"
    try:
        if int(load_json(p6,{}).get("pair_nodes",0)) <= 0:
            return "P6"
    except Exception:
        return "P6"

    p7=Path("automation/evidence/P7_STRATEGY_MATRIX.json")
    if not p7.exists():
        return "P7"

    p8=Path("automation/evidence/P8_FEATURE_SNAPSHOT.json")
    if not p8.exists():
        return "P8"
    try:
        if int(load_json(p8,{}).get("pair_groups",0)) <= 0:
            return "P8"
    except Exception:
        return "P8"

    p9=Path("automation/evidence/P9_ECONOMIC_SCREEN.json")
    if not p9.exists():
        return "P9"

    return task

def sync_stage_metadata(state):
    """Keep human-readable stage metadata aligned with the authoritative critical stage."""
    stages = state.setdefault("stages", {})
    current = state.get("critical_stage", "P2")
    order = ["P2"] + PROMOTION
    if current not in order:
        current_index = 0
    else:
        current_index = order.index(current)

    for index, stage in enumerate(order):
        entry = stages.setdefault(stage, {})
        if stage == "P11":
            entry["mode"] = "SHADOW"
            entry["status"] = "LOCKED" if current_index < order.index("P11") else entry.get("status", "PREPARE")
            continue
        if index < current_index:
            entry["status"] = "CLOSED"
        elif index == current_index:
            entry["mode"] = "CRITICAL"
            entry["status"] = "OPEN"
        else:
            entry["mode"] = "SHADOW"
            entry["status"] = "PREPARE"

    if state.get("research_gate") == "P2_CLOSED":
        stages.setdefault("P2", {})["status"] = "CLOSED"
        if current == "P2":
            stages["P2"]["mode"] = "CRITICAL"


def p2_gate(state):
    conditions={
      'storage_checkpoint': Path('chains/polygon-pos/P2_ERC1967_STORAGE_RUN_4.md').exists(),
      'derived_verified': Path('automation/evidence/P2_DERIVED_LATEST.json').exists() and load_json(Path('automation/evidence/P2_DERIVED_LATEST.json'),{}).get('evidence_state')=='VERIFIED',
      'control_verified': Path('automation/evidence/P2_CONTROL_FUNCTION_LATEST.json').exists() and load_json(Path('automation/evidence/P2_CONTROL_FUNCTION_LATEST.json'),{}).get('evidence_state')=='VERIFIED',
      'provenance_replayed': Path('automation/evidence/P2_PROVENANCE_LATEST.json').exists() and load_json(Path('automation/evidence/P2_PROVENANCE_LATEST.json'),{}).get('status')=='REPLAYED'
    }
    # This is intentionally strict. Unknown creation provenance outside known historical txs
    # keeps the gate open until a future provenance task closes it.
    closed=all(conditions.values())
    return closed,conditions

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--max-critical',type=int,default=1); ap.add_argument('--max-shadow',type=int,default=2); ap.add_argument('--time-budget',type=int,default=780); args=ap.parse_args()
    state=load_json(STATE,{'schema_version':1,'critical_stage':'P2','research_gate':'P2_OPEN','shadow_lane':True,'stages':{},'tasks':{},'last_progress_signature':'','last_run':None})
    old_gate=state.get('research_gate','P2_OPEN'); old_stage=state.get('critical_stage','P2'); old_stage_metadata=json.dumps(state.get('stages',{}),sort_keys=True); started=time.time(); executed=[]
    if state.get('research_gate') != 'P2_CLOSED':
        critical_list=CRITICAL_P2
        critical_cursor=int(state.get('cursors',{}).get('critical',0))
        attempts=0
        while attempts < len(critical_list) and len([x for x in executed if x in critical_list]) < args.max_critical:
            task=critical_list[critical_cursor % len(critical_list)]
            critical_cursor=(critical_cursor+1) % len(critical_list)
            attempts += 1
            if critical_task_complete(task, state):
                continue
            ts=task_state(state,task)
            epoch=current_code_epoch()
            revision=TASK_REVISIONS.get(task)
            if ts.get('code_epoch') != epoch or (revision and ts.get('revision') != revision):
                ts['code_epoch']=epoch
                if revision:
                    ts['revision']=revision
                ts['cooldown_until']=0
            if ts.get('cooldown_until',0)>time.time(): continue
            result=execute(task); ts['attempts']=ts.get('attempts',0)+1; ts['last_run']=now(); ts['ok']=bool(result.get('ok'))
            ts['last_result_summary']=str(result)[-4000:]
            if ts['ok']: ts['last_error']=''; ts['cooldown_until']=0
            else: ts['last_error']=str(result)[-1500:]; ts['cooldown_until']=time.time()+min(3600,300*(2**min(ts['attempts'],4)))
            executed.append(task)
            if time.time()-started>args.time_budget: break
        state.setdefault('cursors',{})['critical']=critical_cursor
    else:
        current=state.get('critical_stage','P3')
        if current in PROMOTION and current not in ('P11',):
            ts=task_state(state,current)
            epoch=current_code_epoch()
            revision=TASK_REVISIONS.get(current)
            if ts.get('code_epoch') != epoch or (revision and ts.get('revision') != revision):
                ts['code_epoch']=epoch
                if revision:
                    ts['revision']=revision
                ts['cooldown_until']=0
            if ts.get('cooldown_until',0)<=time.time():
                result=execute(current); ts['attempts']=ts.get('attempts',0)+1; ts['last_run']=now(); ts['ok']=bool(result.get('ok')); ts['last_result_summary']=str(result)[-4000:]
                if ts['ok']: ts['last_error']=''; ts['cooldown_until']=0
                else: ts['last_error']=str(result)[-1500:]; ts['cooldown_until']=time.time()+min(3600,300*(2**min(ts['attempts'],4)))
                executed.append(current)
    

    shadow_run=0
    shadow_cursor=int(state.get('cursors',{}).get('shadow',0))
    attempts=0

    # Critical-stage acceleration mode: while an active promotion gate is open,
    # spend the bounded execution budget on the critical stage only. Shadow work
    # is resume-safe and will automatically resume once the critical gate closes.
    current_critical = state.get('critical_stage')
    critical_open = (
        state.get('research_gate') == 'P2_CLOSED'
        and current_critical in PROMOTION
        and not stage_ready(current_critical)
    )
    effective_shadow_limit = 0 if critical_open else args.max_shadow

    while attempts < len(SHADOW) and shadow_run < effective_shadow_limit and time.time()-started <= args.time_budget:
        task=SHADOW[shadow_cursor % len(SHADOW)]
        shadow_cursor=(shadow_cursor+1) % len(SHADOW)
        task=shadow_dependency_override(task)
        attempts += 1
        ts=task_state(state,task)
        epoch=current_code_epoch()
        if ts.get('code_epoch') != epoch:
            ts['code_epoch']=epoch
            ts['cooldown_until']=0
        if ts.get('cooldown_until',0)>time.time(): continue
        result=execute(task); ts['attempts']=ts.get('attempts',0)+1; ts['last_run']=now(); ts['ok']=bool(result.get('ok')); ts['last_result_summary']=str(result)[-3500:]
        if ts['ok']: ts['last_error']=''; ts['cooldown_until']=0
        else: ts['last_error']=str(result)[-1500:]; ts['cooldown_until']=time.time()+min(3600,300*(2**min(ts['attempts'],4)))
        shadow_run+=1; executed.append(task)
    state.setdefault('cursors',{})['shadow']=shadow_cursor
    closed,conditions=p2_gate(state)
    state['research_gate']='P2_CLOSED' if closed else 'P2_OPEN'
    if closed:
        current=state.get('critical_stage','P2')
        if current=='P2': state['critical_stage']='P3'
        else:
            idx=PROMOTION.index(current) if current in PROMOTION else 0
            if stage_ready(current) and idx < len(PROMOTION)-1:
                state['critical_stage']=PROMOTION[idx+1]
    else:
        state['critical_stage']='P2'
    sync_stage_metadata(state)
    state.setdefault('cursors',{'critical':0,'shadow':0})
    state['last_run']=now()
    stage_metadata_changed = old_stage_metadata != json.dumps(state.get('stages',{}),sort_keys=True)
    commit_required = (
        old_gate!=state['research_gate']
        or old_stage!=state['critical_stage']
        or stage_metadata_changed
    )
    state['commit_required']=False
    state['last_progress_signature']=json.dumps({'gate':state['research_gate'],'tasks':{k:v.get('attempts') for k,v in state['tasks'].items()},'executed':executed},sort_keys=True)
    report={'time':now(),'critical_stage':state['critical_stage'],'research_gate':state['research_gate'],'commit_required':commit_required,'p2_conditions':conditions,'executed':executed,'task_states':state['tasks'],'shadow_lane':state.get('shadow_lane',True)}
    save_json(STATE,state); save_json(REPORT,report)
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__': main()