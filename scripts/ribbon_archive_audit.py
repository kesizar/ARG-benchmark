"""Bounded public-access audit; never turns an X profile snapshot into a game."""
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
import json, hashlib, re, shutil, urllib.request, asyncio
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1]; T='ribbon-archive'; J=R/'judge'/T; S=J/'source'
class Parser(HTMLParser):
 def __init__(self): super().__init__(); self.links=[]; self.scripts=[]; self.media=[]; self.text=[]; self.skip=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('script','style'): self.skip+=1
  if tag=='a' and a.get('href'): self.links.append(a['href'])
  if tag=='script' and a.get('src'): self.scripts.append(a['src'])
  if tag in ('img','video','source'):
   self.media.append({'tag':tag,**{k:v for k,v in a.items() if k in ('src','srcset','poster','alt')}})
 def handle_endtag(self,tag):
  if tag in ('script','style'): self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip and data.strip(): self.text.append(data.strip())
def w(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
async def main():
 S.mkdir(parents=True,exist_ok=True); src=R/'ARG-packs/verify-416/bodies/181.html'; b=src.read_bytes(); (S/'original.html').write_bytes(b)
 raw=b.decode(); p=Parser(); p.feed(raw)
 (S/'visible-text.txt').write_text('\n'.join(p.text),encoding='utf8')
 audit={'record_id':'base664:0181','timestamp_utc':datetime.now(timezone.utc).isoformat(),'snapshot':{'path':src.relative_to(R).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'html_closed':'</html>' in raw,'title':re.findall(r'<title>(.*?)</title>',raw),'status_links':sorted(set(x for x in p.links if '/status/' in x)),'links':sorted(set(p.links)),'external_scripts':p.scripts,'media':p.media,'tweet_elements':raw.count('data-testid="tweet"'),'has_completion_logic':False},'http':[],'browser':[]}
 url='https://x.com/ribbonarchive05'
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as q:
   body=q.read();(S/'live-http.html').write_bytes(body);audit['http'].append({'url':url,'status':q.status,'final_url':q.url,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
 except Exception as e: audit['http'].append({'url':url,'error':repr(e)})
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,channel='msedge');page=await browser.new_page(); row={'url':url};audit['browser'].append(row)
  try:
   q=await page.goto(url,wait_until='domcontentloaded',timeout=25000); await page.wait_for_timeout(3000)
   row.update(status=q.status if q else None,final_url=page.url,title=await page.title(),body=(await page.locator('body').inner_text())[:10000]);(S/'live-browser.html').write_text(await page.content(),encoding='utf8');await page.screenshot(path=str(S/'live-browser.png'))
  except Exception as e:row['error']=str(e)
  await browser.close()
 audit['snapshot']['dynamic_assets']=sorted(set(re.findall(r'https://abs\.twimg\.com/[^\s"<>]+',raw)))
 audit['public_recovery']=[]
 for i,path in enumerate(audit['snapshot']['status_links']+['/ribbonarchive05/with_replies','/ribbonarchive05/media','/ribbonarchive05/about']):
  u='https://x.com'+path; row={'url':u};audit['public_recovery'].append(row)
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=15) as q:
    body=q.read();target=S/f'public-{i}.html';target.write_bytes(body); pp=Parser();pp.feed(body.decode('utf8',errors='replace')); (S/f'public-{i}.txt').write_text('\n'.join(pp.text),encoding='utf8')
    row.update(status=q.status,final_url=q.url,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),path=target.relative_to(R).as_posix(),status_links=sorted(set(x for x in pp.links if '/status/' in x)),media=pp.media)
  except Exception as e:row['error']=repr(e)
 w(S/'access-audit.json',audit)
 print(json.dumps({'snapshot':{k:audit['snapshot'][k] for k in ('bytes','title','status_links','tweet_elements')},'http':audit['http'],'browser':audit['browser']},ensure_ascii=True))
if __name__=='__main__':asyncio.run(main())
