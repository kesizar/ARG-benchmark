import pathlib,json,subprocess,hashlib
root=pathlib.Path('judge/youlun-xia/recovery');inv=json.loads((root/'graph-inventory.json').read_text(encoding='utf-8'));manifest=json.loads((root/'media-download.json').read_text(encoding='utf-8'));expected={x['cid']:x for x in manifest};rows=[]
for cid in inv['unique_video_cids']:
 p=pathlib.Path(f'tasks/youlun-xia/media/{cid}.mp4');b=p.read_bytes();q=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_name,width,height','-of','json',str(p)],capture_output=True,text=True)
 rows.append({'cid':cid,'bytes':len(b),'sha256_matches':hashlib.sha256(b).hexdigest()==expected[cid]['sha256'],'probe_returncode':q.returncode,'probe':json.loads(q.stdout) if q.returncode==0 else q.stderr})
a={'expected_videos':len(inv['unique_video_cids']),'files_verified':len(rows),'all_hashes_match':all(x['sha256_matches'] for x in rows),'all_probe_success':all(x['probe_returncode']==0 for x in rows),'total_bytes':sum(x['bytes'] for x in rows),'videos':rows};(root/'media-validation.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in a.items() if k!='videos'})
