"""Extract review contact sheets from existing media, without network."""
import pathlib,json,subprocess,concurrent.futures
from PIL import Image,ImageDraw
R=pathlib.Path('judge/youlun-xia/recovery');O=R/'frames';O.mkdir(exist_ok=True)
manifest=json.loads((R/'media-validation.json').read_text(encoding='utf-8'))
def work(row):
 cid=row['cid'];d=O/str(cid);d.mkdir(exist_ok=True)
 if not list(d.glob('*.jpg')):
  subprocess.run(['ffmpeg','-v','error','-i',f'tasks/youlun-xia/media/{cid}.mp4','-vf','fps=1/4','-q:v','2',str(d/'%04d.jpg')],check=True)
 pics=sorted(d.glob('*.jpg'));w=480;h=380;cols=3
 im=Image.new('RGB',(w*cols,h*((len(pics)+cols-1)//cols)), 'white');dr=ImageDraw.Draw(im)
 for i,p in enumerate(pics):
  im.paste(Image.open(p),(i%cols*w,i//cols*h));dr.text((i%cols*w+5,i//cols*h+361),f'{cid} / ~{i*4+2}s',fill='black')
 im.save(O/f'{cid}.jpg')
 return {'cid':cid,'samples':len(pics),'sheet':str(O/f'{cid}.jpg')}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: rows=list(ex.map(work,manifest['videos']))
(R/'frame-review-index.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print({'sheets':len(rows),'frames':sum(r['samples'] for r in rows)})
