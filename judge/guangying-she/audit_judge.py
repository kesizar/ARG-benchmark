"""Evaluator-only pure oracle; original game code is never modified."""
ORDER=[f'p{i}' for i in range(1,9)]
def evaluate(state,route='',text=''):
 s=state or {};eligible=s.get('hintMode')=='off';wall=eligible and s.get('solved') is True and s.get('checkedCount',0)>0 and s.get('slots')==ORDER
 return {'critical_checkpoints_reached':int(wall),'optional_darkroom':eligible and s.get('darkroom') is True,'ending_reached':wall and route=='#/opening' and '名 誉 观 展 证' in text}
