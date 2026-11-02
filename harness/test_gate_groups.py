import unittest
from harness.judge import Judge

class GateGroupTests(unittest.TestCase):
    def config(self):
        ids=[f's{i}' for i in range(12)]+[f'c{i}' for i in range(3)]+[f'f{i}' for i in range(3)]
        return {'hooks':{},'checkpoints':[{'id':x,'hook':x} for x in ids],
                'routes':[{'id':'done','gates':['f0','f1','f2'],
                    'gate_groups':[{'ids':[f's{i}' for i in range(12)],'required':10},
                                   {'ids':['c0','c1','c2'],'required':1}],
                    'ending':{'hook':'end'}}]}

    def test_minimum_subset_gets_full_credit_without_extra_points(self):
        j=Judge(self.config(),'sample')
        self.assertEqual(j.score()['route_progress'],0)
        j.values={**{f's{i}':True for i in range(10)},'c1':True,'f0':True,'f1':True,'f2':True,'end':True}
        j.update(1)
        self.assertEqual(j.score()['route_progress'],1)
        self.assertEqual(j.score()['checkpoints_reached'],14)
        self.assertEqual(j.score()['checkpoints_total'],18)
        j.values.update({'s10':True,'s11':True,'c0':True,'c2':True});j.update(2)
        self.assertEqual(j.score()['route_progress'],1)

    def test_group_only_route_is_partial_before_threshold(self):
        cfg=self.config();cfg['routes'][0]['gates']=[]
        j=Judge(cfg,'sample');j.values={**{f's{i}':True for i in range(9)},'c0':True};j.update(1)
        self.assertEqual(j.score()['route_progress'],round(10/11,4))
        self.assertFalse(j.score()['ending_reached'])

    def test_invalid_and_overlapping_groups_rejected(self):
        for ids,required in [(['missing'],1),(['s0','s0'],1),(['f0'],1),(['s0'],2),(['s0'],True)]:
            cfg=self.config();cfg['routes'][0]['gate_groups']=[{'ids':ids,'required':required}]
            with self.assertRaises(ValueError):Judge(cfg,'sample')
