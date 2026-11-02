"""Local-only source graph audit. No downloads or model calls."""
import json,pathlib,collections,shutil
R=pathlib.Path('judge/youlun-xia/recovery')
nodes={int(p.stem):json.loads(p.read_bytes())['data'] for p in (R/'graph').glob('*.json')}
lines=[]; cids=collections.defaultdict(list)
edge_cid={1:142802415}
for n in nodes.values():
    for q in n.get('edges',{}).get('questions',[]):
        for c in q.get('choices',[]):
            assert edge_cid.setdefault(c['id'],c['cid'])==c['cid']
for eid,n in sorted(nodes.items()):
    story=n.get('story_list',[])
    current=next((s for s in story if s.get('is_current')),story[-1] if story else {})
    cid=edge_cid[eid];cids[cid].append(eid)
    qs=n.get('edges',{}).get('questions',[])
    lines.append({'edge':eid,'cid':cid,'title':n.get('title'),'leaf':n.get('is_leaf'),'questions':qs})
(R/'audit-graph.json').write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding='utf-8')
text=[]
for cid,ids in cids.items():
    variants=[]
    for i in ids:
        row=next(r for r in lines if r['edge']==i)
        opts=['%s -> %s'%(c.get('option'),c['id']) for q in row['questions'] for c in q.get('choices',[])]
        if opts not in variants:variants.append(opts)
    text.append(f'CID {cid}, edges {ids}\n'+ '\n'.join(' | '.join(v) for v in variants))
(R/'choices-audit.txt').write_text('\n\n'.join(text),encoding='utf-8')
print(json.dumps({'nodes':len(nodes),'cids':len(cids),'leaves':[(r['edge'],r['cid']) for r in lines if r['leaf']], 'tools':{s:shutil.which(s) for s in ['ffmpeg','ffprobe','tesseract']}}))
