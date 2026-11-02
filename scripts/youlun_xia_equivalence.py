"""Finite graph bisimulation proof, retaining all source nodes in the actual player."""
import collections, hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/'tasks/youlun-xia/graph.json'
G={int(k):v for k,v in json.loads(P.read_text(encoding='utf-8')).items()}
S=ROOT/'judge/youlun-xia/recovery/graph'
source_hashes={}
for n,row in G.items():
    raw=(S/f'{n}.json').read_bytes();source=json.loads(raw)['data']
    assert row['questions']==source.get('edges',{}).get('questions',[])
    assert row['title']==source.get('title') and row['leaf']==source.get('is_leaf')
    assert bool(row['leaf'])==(not bool(row['questions']))
    source_hashes[str(n)]=hashlib.sha256(raw).hexdigest()
def signature(n, classes=None):
    row=G[n]
    return (row['cid'],bool(row['leaf']),tuple(
      (q['type'],q['start_time_r'],q['duration'],q['pause_video'],q['title'],tuple(
        (c['option'],c.get('condition',''),c.get('native_action',''),c['cid'],
         None if classes is None else classes[c['id']]) for c in q['choices']))
      for q in row['questions']))
def classify(signatures):
    unique={s:i for i,s in enumerate(dict.fromkeys(signatures.values()))}
    return {n:unique[s] for n,s in signatures.items()}
C=classify({n:signature(n) for n in G});rounds=[]
while True:
    rounds.append(len(set(C.values())))
    new=classify({n:signature(n,C) for n in G})
    if new==C:break
    C=new
groups=collections.defaultdict(list)
for n,c in C.items():groups[c].append(n)
for n,row in G.items():
    for q in row['questions']:
        for c in q['choices']:
            assert c['condition']=='' and c.get('native_action','')==''
            assert c['platform_action']==f"JUMP {c['id']} {c['cid']}"
            assert G[c['id']]['cid']==c['cid']
out={'graph_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'source_nodes':len(G),
     'source_question_metadata_equal':True,'source_response_sha256':source_hashes,
     'source_arcs':sum(len(q['choices']) for r in G.values() for q in r['questions']),
     'equivalence_class_count':len(groups),'refinement_class_counts':rounds,
     'proof_scope':'Same source CID, leaf flag, ordered question timing/type/title/options, blank conditions/native actions, and successor classes. Source title/is_default/platform target IDs are excluded: title/is_default are not displayed/used in the local player, JUMP targets are checked separately. This is local adaptation behavioral equivalence, not audiovisual identity beyond CID or original-runtime equivalence.',
     'classes':[{'class':c,'representative':nodes[0],'cid':G[nodes[0]]['cid'],'nodes':nodes,
       'successors':[[C[ch['id']] for ch in q['choices']] for q in G[nodes[0]]['questions']]} for c,nodes in sorted(groups.items())]}
(ROOT/'judge/youlun-xia/recovery/graph-equivalence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print({k:out[k] for k in ('source_nodes','source_arcs','equivalence_class_count','refinement_class_counts')})
