from __future__ import annotations
import ast, json, sys
from pathlib import Path
import yaml

BASE=Path(__file__).resolve().parent
FILES=[BASE/'Decision & Partner Agent 1_FRONTEND_ALIGNED.yml',BASE/'Decision & Partner Agent 2_BACKEND_ALIGNED.yml']


def declared_outputs(node):
    d=node.get('data',{}); typ=d.get('type')
    if typ=='start': return {v.get('variable') for v in d.get('variables',[])}
    if typ=='code': return set((d.get('outputs') or {}).keys())
    if typ=='http-request': return {'body','status_code','headers','files'}
    if typ=='llm': return {'text','usage','finish_reason','structured_output'}
    if typ=='variable-aggregator': return {'output'}
    return set()


def check(path):
    data=yaml.safe_load(path.read_text(encoding='utf-8'))
    g=data['workflow']['graph']; nodes={str(n['id']):n for n in g['nodes']}; errors=[]
    for nid,n in nodes.items():
        d=n.get('data',{})
        if d.get('type')=='code':
            try:
                tree=ast.parse(d.get('code',''))
            except SyntaxError as exc: errors.append(f'Code syntax {nid} {d.get("title")}: {exc}'); continue
            mains=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name=='main']
            if len(mains)!=1: errors.append(f'Code node {nid} has {len(mains)} main functions')
        if '}import json' in d.get('code',''): errors.append(f'Code node {nid} contains }}import json')
    # input selectors and End selectors
    for nid,n in nodes.items():
        d=n.get('data',{})
        selectors=[]
        for v in d.get('variables') or []:
            if isinstance(v,dict) and v.get('value_selector'): selectors.append(tuple(v['value_selector']))
        if d.get('type')=='end':
            for o in d.get('outputs') or []: selectors.append(tuple(o['value_selector']))
        if d.get('type')=='variable-aggregator':
            selectors.extend(tuple(v) for v in d.get('variables') or [])
        for src,out in selectors:
            src=str(src)
            if src not in nodes: errors.append(f'{nid}: missing source node {src}.{out}'); continue
            if out not in declared_outputs(nodes[src]): errors.append(f'{nid}: source output missing {src}.{out}')
    # graph reachability
    adj={nid:[] for nid in nodes}; rev={nid:[] for nid in nodes}
    for e in g['edges']:
        s,t=str(e['source']),str(e['target'])
        if s not in nodes or t not in nodes: errors.append(f'Broken edge {s}->{t}'); continue
        adj[s].append(t); rev[t].append(s)
    starts=[nid for nid,n in nodes.items() if n['data'].get('type')=='start']
    ends=[nid for nid,n in nodes.items() if n['data'].get('type')=='end']
    reach=set(starts); stack=list(starts)
    while stack:
        s=stack.pop()
        for t in adj[s]:
            if t not in reach: reach.add(t); stack.append(t)
    can=set(ends); stack=list(ends)
    while stack:
        t=stack.pop()
        for s in rev[t]:
            if s not in can: can.add(s); stack.append(s)
    for nid in sorted(reach-can): errors.append(f'Reachable node has no End path: {nid} {nodes[nid]["data"].get("title")}')
    # output uniqueness
    names=[]
    for eid in ends: names += [o['variable'] for o in nodes[eid]['data'].get('outputs') or []]
    dup=sorted({n for n in names if names.count(n)>1})
    if dup: errors.append(f'Duplicate End output names: {dup}')
    return data,errors


def exec_code(data,title,kwargs):
    node=next(n for n in data['workflow']['graph']['nodes'] if n['data'].get('title')==title)
    ns={}; exec(node['data']['code'],ns)
    return ns['main'](**kwargs)

report=[]; loaded={}
for p in FILES:
    d,errors=check(p); loaded[p.name]=d
    report.append(f'{p.name}: '+('PASS' if not errors else 'FAIL'))
    report.extend('  - '+e for e in errors)

# Simulate the Agent 1 frontend compatibility contract.
a1=loaded[FILES[0].name]
sample_package={
    'decision_id':'DEC-DRAFT-CON-004-TEST','source_log_id':'LOG-CON-004-DEC-DRAFT-TEST','contract_id':'CON-004',
    'recommendation':'CONDITIONAL_ACCEPT','final_decision':'CONDITIONAL_ACCEPT','reason_1':'Margin 24% below 28%.',
    'reason_2':'Risk CRITICAL; Founder confirmation required.','reason_3':'VietinBank working capital option is the best fit.',
    'protective_condition':'Founder must confirm Hold or Override before external submission.','requested_amount':710000000,
    'recommended_partner':'VietinBank','recommended_product':'Working Capital Credit Line','required_approvals':['FOUNDER_REVIEW_FINANCE'],
    'confidence_score':0.71,'risk_level':'CRITICAL','risk_flags':['RR-001','RR-002','RR-003'],
    'decision_card':{'decision_id':'DEC-DRAFT-CON-004-TEST','recommendation':'CONDITIONAL_ACCEPT','reasons':['Margin 24% below 28%.','Risk CRITICAL; Founder confirmation required.','VietinBank working capital option is the best fit.'],'protective_condition':'Founder must confirm Hold or Override before external submission.','confidence_score':0.71,'risk_level':'CRITICAL'},
    'finance_result':{'total_order_revenue':3100000000,'total_estimated_cost':2356000000,'computed_margin':0.24,'target_margin':0.28,'maximum_funding_need':710000000,'months_below_reserve':['2026-06','2026-07','2026-08'],'financial_flags':['RR-002','RR-003'],'confidence_score':0.75,'cashflow_summary':{'monthly_summary':[{'month':'2026-06','expected_cash_in':100,'expected_cash_out':200,'projected_closing_cash':-160000000,'cash_reserve_minimum':550000000}] }},
    'finance_metrics':{'computed_margin':0.24,'target_margin':0.28,'maximum_funding_need':710000000,'months_below_reserve':['2026-06','2026-07','2026-08'],'confidence_score':0.75,'flags':['RR-002','RR-003'],'analysis':'OpenAI finance summary'},
    'risk_summary':{'risk_level':'CRITICAL','risk_flags':['RR-001'],'required_approvals':['FOUNDER_CONFIRM_TRANSACTION_HOLD'],'confidence_score':0.74},
    'partner_summary':{'recommended_partner':'VietinBank','recommended_product':'Working Capital Credit Line'},
    'package_status':'draft_ready_for_founder','session_status':'WAITING_FOUNDER_DECISION'
}
out=exec_code(a1,'25. BUILD FRONTEND-COMPATIBLE OUTPUT',{'final_package_json':json.dumps(sample_package)})
required=['status','decision','finance_result','computed_margin','maximum_funding_need','risk_level','requested_amount','decision_package']
missing=[k for k in required if k not in out]
if missing: report.append('Agent1 frontend contract simulation: FAIL missing '+','.join(missing))
elif out['computed_margin']!=0.24 or out['maximum_funding_need']!=710000000 or out['risk_level']!='CRITICAL':
    report.append('Agent1 frontend contract simulation: FAIL values')
else: report.append('Agent1 frontend contract simulation: PASS')

# Simulate Agent 2 loading Agent 1 package from agent_decisions.output_ref using only contract_id.
a2=loaded[FILES[1].name]
audit=[{'log_id':'LOG-CON-004-DEC-DRAFT-TEST','trace_id':'TRACE-CON-004-TEST','output_ref':json.dumps(sample_package)}]
out2=exec_code(a2,'PARSE DECISION PACKAGE',{
    'decision_package_input':'','source_audit_body':json.dumps(audit),'decision_id_input':'','contract_id_input':'CON-004',
    'founder_decision_input':'approve','external_send_confirmation_input':'confirm'
})
if out2.get('parse_status')=='completed' and out2.get('decision_id')=='DEC-DRAFT-CON-004-TEST' and out2.get('requested_amount')==710000000:
    report.append('Agent2 backend contract simulation: PASS')
else:
    report.append('Agent2 backend contract simulation: FAIL '+json.dumps(out2,ensure_ascii=False))

overall=not any('FAIL' in line for line in report)
report.append('OVERALL: '+('PASS' if overall else 'FAIL'))
print('\n'.join(report))
(BASE/'validation_report.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
sys.exit(0 if overall else 1)
