from pathlib import Path
p=Path('judge/guiyihui-meimei/checkpoint-spec.json');import json
x=json.loads(p.read_text(encoding='utf-8'));x['photo_precondition']='21、22 须观察照片3经反色/亮度调整显影；前置只要求曾显示，非完整路线必经。';p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
p=Path('tasks/guiyihui-meimei/README.md');s=p.read_text(encoding='utf-8');s+='\n照片第 21、22 点还要求曾在照片窗口显影。正常通关时最终结局可绕过所有推理点，结局达成与关卡得分分别记录。\n';p.write_text(s,encoding='utf-8')
