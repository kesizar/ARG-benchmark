"""Independent audit of saved visible outcomes; no source state writes, no inference points."""
def judge(visible_end,title,body=''):
 names={'💎 完美清算':('perfect','good'),'⚔️ 干净利落':('clean','good'),'🩸 惨胜':('bitter','normal'),'🌪 鱼死网破':('both','bad'),'💀 被反杀':('killed','bad')}
 route,tier=names.get(title,(None,None)) if visible_end else (None,None)
 return {'route':route,'tier':tier,'egg':route=='perfect' and '【隐藏彩蛋】' in body,'reasoning_points':0,'formal_reasoning_success':False}
