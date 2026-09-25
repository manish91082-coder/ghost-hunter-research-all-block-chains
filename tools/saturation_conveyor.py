#!/usr/bin/env python3
"""Manifest-driven autonomous evidence conveyor for Polygon P2-P11.
Runs bounded work, checkpoints state, preserves failures, and never promotes
a research gate from a single failed/partial observation.
"""
import argparse, json, os, subprocess, sys, time, shutil
from pathlib import Path

STATE=Path('automation/saturation_state.json')
PLAN=Path('automation/saturation_plan.json')
EVID=Path('automation/evidence')
REPORT=Path('automation/conveyor_report.json')

CRITICAL_P2=['P2_REGRESSION','P2_DERIVED','P2_CONTROL_FUNCTION','P2_PROVENANCE']
PROMOTION=['P3','P4','P5','P6','P7','P8','P9','P10']
SHADOW=['P3','P4','P5','P6','P7','P8','P9','P10']
WORKER=Path('tools/polygon_universe_worker.py')

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
    cmd=['python','chains/polygon-pos/polygon_p2_control_function_verifier.py','--rpc-pool-file','chains/polygon-pos/rpc_pool.txt','--min-request-interval','1.0','--min-head-endpoints','2','--min-probe-endpoints','2','--recovery-rounds','2','--stale-block-tolerance','2','--target-file','chains/polygon-pos/p2_control_function_targets.txt']
    a=run(cmd,timeout=800)
    b=run(['python','chains/polygon-pos/polygon_p2_control_function_reconciliation.py'],timeout=60)
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
    started=time.time(); executed=[]
    critical_list = CRITICAL_P2 if state.get('research_gate') != 'P2_CLOSED' else PROMOTION
    critical_cursor = int(state.get('cursors',{}).get('critical',0))
    attempts=0
    while attempts < len(critical_list) and len([x for x in executed if x in critical_list]) < args.max_critical:
        task=critical_list[critical_cursor % len(critical_list)]
        critical_cursor=(critical_cursor+1) % len(critical_list)
        attempts += 1
        ts=task_state(state,task)
        if ts.get('cooldown_until',0)>time.time(): continue
        result=execute(task); ts['attempts']=ts.get('attempts',0)+1; ts['last_run']=now(); ts['ok']=bool(result.get('ok'))
        ts['last_result_summary']=str(result)[-4000:]
        if ts['ok']: ts['last_error']=''; ts['cooldown_until']=0
        else: ts['last_error']=str(result)[-1500:]; ts['cooldown_until']=time.time()+min(3600,300*(2**min(ts['attempts'],4)))
        executed.append(task)
        if time.time()-started>args.time_budget: break
    state.setdefault('cursors',{})['critical']=critical_cursor

    shadow_run=0
    shadow_cursor=int(state.get('cursors',{}).get('shadow',0))
    attempts=0
    while attempts < len(SHADOW) and shadow_run < args.max_shadow and time.time()-started <= args.time_budget:
        task=SHADOW[shadow_cursor % len(SHADOW)]
        shadow_cursor=(shadow_cursor+1) % len(SHADOW)
        attempts += 1
        ts=task_state(state,task)
        if ts.get('cooldown_until',0)>time.time(): continue
        result=execute(task); ts['attempts']=ts.get('attempts',0)+1; ts['last_run']=now(); ts['ok']=bool(result.get('ok')); ts['last_result_summary']=str(result)[-3500:]
        if ts['ok']: ts['last_error']=''; ts['cooldown_until']=0
        else: ts['last_error']=str(result)[-1500:]; ts['cooldown_until']=time.time()+min(3600,300*(2**min(ts['attempts'],4)))
        shadow_run+=1; executed.append(task)
    state.setdefault('cursors',{})['shadow']=shadow_cursor
    closed,conditions=p2_gate(state)
    state['research_gate']='P2_CLOSED' if closed else 'P2_OPEN'
    state['critical_stage']='P3' if closed else 'P2'
    state.setdefault('cursors',{'critical':0,'shadow':0})
    state['last_run']=now()
    state['last_progress_signature']=json.dumps({'gate':state['research_gate'],'tasks':{k:v.get('attempts') for k,v in state['tasks'].items()},'executed':executed},sort_keys=True)
    report={'time':now(),'critical_stage':state['critical_stage'],'research_gate':state['research_gate'],'p2_conditions':conditions,'executed':executed,'task_states':state['tasks'],'shadow_lane':state.get('shadow_lane',True)}
    save_json(STATE,state); save_json(REPORT,report)
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__': main()