from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'scripts/xinshiji_branches_ui.py').read_text('utf8')
s=s.replace("out=root/'judge/xinshiji/recovery/branches'","out=root/'judge/xinshiji/recovery/branches-continuation'")
s=s.replace("ctx=b.new_context(viewport=", "ctx=b.new_context(storage_state=str(root/'judge/xinshiji/recovery/branches/state.json'),viewport=")
a=s.index('  start();f=chat()');z=s.index('  # Survey rejection')
s=s[:a]+"  p.goto('http://127.0.0.1:8823/index.html');click(p,'#continueBtn');wait(1200);f=chat();mark('resumed_native_storage_manager8',step=p.evaluate(\"localStorage.getItem('sunStep')\"))\n"+s[z:]
s=s.replace("click(f,'[onclick=\"followXiaoyou()\"]')","click(f,'#followBtn')")
s=s.replace("click(main(),'.browser-tab[data-tab=\"leyuan\"]');f=", "search('新世纪乐园');f=")
(r/'scripts/xinshiji_branches_continue.py').write_text(s,encoding='utf8')
print('Continuation uses browser-native captured storage, normal index continue, no injected answers/state.')
