from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'scripts/xinshiji_mandatory_judge_ui.py').read_text('utf8')
s=s.replace("recovery/mandatory-judge", "recovery/garden-delta")
a=s.index("  for k in ['flower3'");z=s.index("  dark=main.frame_locator",a)
s=s[:a]+'''  for _ in range(3):flower.locator('#butterfly').click(force=True)
  assert not probe.sample(p)['hooks']['garden'];mark('garden_wrong_all_closed_no_credit')
  for k in ['flower1','flower3','flower4','flower5']:flower.locator('#'+k).click(force=True)
  for _ in range(3):flower.locator('#sun').click(force=True)
  for _ in range(3):flower.locator('#butterfly').click(force=True)
  assert not probe.sample(p)['hooks']['garden'];mark('garden_wrong_pink_open_no_credit')
  flower.locator('#flower1').click(force=True)
  for _ in range(2):flower.locator('#butterfly').click(force=True)
  assert not probe.sample(p)['hooks']['garden'];mark('garden_change_resets_butterfly_and_two_insufficient')
  flower.locator('#butterfly').click(force=True);p.wait_for_timeout(1000)
  assert probe.sample(p)['hooks']['garden'];mark('garden_correct_only_third_after_state_repair')
''' + s[z:]
a=s.index("  dark=main.frame_locator");z=s.index(' except Exception as e:',a);s=s[:a]+s[z:]
(r/'scripts/xinshiji_garden_delta_ui.py').write_text(s,encoding='utf8')
print('garden delta verifier ready')
