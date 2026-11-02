from pathlib import Path
import json,shutil,re,difflib
root=Path('.'); dest=root/'tasks/guiyihui-meimei/mirror'; dest.mkdir(parents=True,exist_ok=True)
assets=root/'judge/guiyihui-meimei/assets'; shutil.copytree(assets,dest/'assets',dirs_exist_ok=True)
html=(root/'data/preparation/results/base664-0431-embed.html').read_text(encoding='utf-8'); orig=html
for x in json.loads((root/'judge/guiyihui-meimei/resource-inventory.json').read_text(encoding='utf-8')):
 assert 'error' not in x
 html=html.replace(x['url'],'assets/'+Path(x['file'].replace('\\','/')).name)
css=(root/'judge/guiyihui-meimei/font-local.css').read_text(encoding='utf-8')
html=re.sub(r"@import url\('https://fonts.googleapis.com/[^']+'\);",lambda m:css,html)
html=re.sub(r'<script type="module" src="https://static.cloudflareinsights.com/[^\n]+</script>','',html)
assert not re.findall(r'https?://(?:cdn\.jsdelivr\.net|images\.pexels\.com|fonts\.googleapis\.com|fonts\.gstatic\.com|static\.cloudflareinsights\.com)',html)
old='''            activePhotoIdx = 1;
            updateLevelUI();
        }

        function triggerUIFeedback'''; new='''            activePhotoIdx = 1;
            updateLevelUI();
            updateTimerUI();
            startGlobalTimer();
        }

        function triggerUIFeedback'''; assert old in html; html=html.replace(old,new,1)
(dest/'index.html').write_text(html,encoding='utf-8')
(root/'judge/guiyihui-meimei/localization.diff').write_text(''.join(difflib.unified_diff(orig.splitlines(True),html.splitlines(True),fromfile='original-embed.html',tofile='localized-index.html')),encoding='utf-8')
print('localized',len(html),'assets',len(list((dest/'assets').iterdir())))
