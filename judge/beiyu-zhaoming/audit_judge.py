"""Independent non-scoring diagnostics for the recovered original. Evaluator only."""
def evaluate(url, visible_text, storage):
 return {'formal_scoring_eligible':False,'reason':'No original answer-validation puzzle gates; visits and nonempty report are insufficient evidence of reasoning.',
 'critical_checkpoints_total':0,'critical_checkpoints_reached':0,'success':False,
 'diagnostics':{'ending_visible':url.endswith('/fugao.html') and '调查结束，你查明了事情的真相，仅此而已' in visible_text,
 'profiles_visited':all(storage.get('visited_'+n)=='1' for n in ['whr1','zyy1','zjg1'])}}
