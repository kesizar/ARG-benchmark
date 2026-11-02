"""Evaluation-side only. Terminal classification audited against original video frames.
No player score flags are accepted; the source graph and journal are checked here.
This provisional evaluator is not yet integrated into the shared harness.
"""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
ROWS=json.loads((ROOT/'recovery/audit-graph.json').read_text(encoding='utf-8'))
GRAPH={r['edge']:r for r in ROWS}
SUCCESS_CID=142813414
def evaluate(state):
    edge=None;expect=1;leaf=None
    try:
        for event in state['events']:
            if event['type']=='enter':
                if event['edge']!=expect:return {'score':0,'valid':False,'reason':'invalid entry'}
                edge=expect;expect=None
            elif event['type']=='choice':
                if event['from']!=edge or expect is not None:return {'score':0,'valid':False,'reason':'invalid transition'}
                options=[c for q in GRAPH[edge]['questions'] for c in q['choices']]
                if not any(c['id']==event['to'] and c['option']==event['option'] for c in options):return {'score':0,'valid':False,'reason':'choice absent from original graph'}
                if event['at']<event['duration']-.45:return {'score':0,'valid':False,'reason':'premature choice'}
                expect=event['to']
            elif event['type']=='leaf':
                if event['edge']!=edge or not GRAPH[edge]['leaf']:return {'score':0,'valid':False,'reason':'invalid terminal'}
                leaf=edge
            else:return {'score':0,'valid':False,'reason':'unknown journal event'}
        complete=leaf is not None and expect is None and state['edge']==leaf and state['ended']
        won=complete and GRAPH[leaf]['cid']==SUCCESS_CID
        return {'score':int(won),'valid':True,'complete':bool(complete),'success':bool(won),'terminal_cid':GRAPH[leaf]['cid'] if complete else None,'scope':'provisional terminal-only; no reasoning checkpoints claimed'}
    except (KeyError,TypeError):return {'score':0,'valid':False,'reason':'malformed journal'}
