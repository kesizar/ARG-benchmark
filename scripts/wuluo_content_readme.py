from pathlib import Path
p=Path('tasks/wuluo-cun/README.md');s=p.read_text(encoding='utf8');old='judge\\wuluo-cun\\verify_sample.py';new='judge\\wuluo-cun\\verify_content_closeout.py';assert old in s;s=s.replace(old,new);s += '\n当前裁判将脚印、石阵、雾中辨向、刻痕、香囊切口和语义近似的亡魂第三问列为诊断，其他 15 项为关键点；两条结局均不评级。题目提示与试错限制详见内容复核。\n';p.write_text(s,encoding='utf8')
