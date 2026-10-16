import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'skill/subscription-quota/scripts'))
from budget import evaluate
from codex_snapshot import normalize
from import_snapshot import convert

NOW = 1792119000

def snapshot(remaining=50, hours=2.5, duration=5):
    return {'schema_version': 1, 'route': 'test', 'scope_verified': True,
        'observed_at': NOW, 'billing': 'subscription', 'evidence': {'source': 'synthetic'},
        'windows': [{'id': 'model', 'remaining_percent': remaining,
                     'window_hours': duration, 'resets_at': NOW+hours*3600}]}

class BudgetTests(unittest.TestCase):
    def test_same_percentage_different_time(self):
        self.assertEqual(evaluate(snapshot(10,2), 'test', NOW)['level'], 'TIGHT')
        self.assertEqual(evaluate(snapshot(10,.25), 'test', NOW)['level'], 'ABUNDANT')

    def test_reference_is_period_specific(self):
        result=evaluate(snapshot(50,84,168), 'test', NOW)
        self.assertAlmostEqual(result['windows'][0]['reference_pph'], 100/168)
        self.assertEqual(result['level'], 'COMFORTABLE')

    def test_user_reference_boundaries(self):
        for rate, expected in [(5.9,'TIGHT'),(6,'CONSERVATIVE'),(12,'COMFORTABLE'),(18,'ABUNDANT')]:
            s=snapshot(60,60/rate,24)
            s['windows'][0]['reference_pph']=12
            self.assertEqual(evaluate(s,'test',NOW)['level'],expected)

    def test_weekly_constraint_wins(self):
        s=snapshot(80,.5)
        s['windows'].append({'id':'weekly','remaining_percent':20,'window_hours':168,'resets_at':NOW+100*3600})
        self.assertEqual(evaluate(s,'test',NOW)['limiting_windows'],['weekly'])
        self.assertEqual(evaluate(s,'test',NOW)['level'],'TIGHT')

    def test_absolute_limit_near_reset(self):
        self.assertEqual(evaluate(snapshot(2,.01),'test',NOW)['level'],'CONSERVATIVE')
        self.assertEqual(evaluate(snapshot(0,.01),'test',NOW)['status'],'EXHAUSTED')

    def test_reset_never_presumed(self):
        self.assertEqual(evaluate(snapshot(20,0),'test',NOW)['status'],'UNKNOWN')

    def test_stale_future_scope_and_billing(self):
        for patch in [{'observed_at':NOW-301},{'observed_at':NOW+31},{'scope_verified':False},
                      {'route':'other'},{'billing':'unknown'},{'evidence':{}}]:
            s=snapshot();s.update(patch)
            self.assertEqual(evaluate(s,'test',NOW)['status'],'UNKNOWN')

    def test_invalid_numbers(self):
        for bad in [float('nan'),float('inf'),-1,101,True,'80']:
            with self.assertRaises(ValueError):evaluate(snapshot(bad),'test',NOW)

    def test_malformed_cycle(self):
        self.assertEqual(evaluate(snapshot(hours=6),'test',NOW)['status'],'UNKNOWN')

    def test_wallet_not_subscription(self):
        s=snapshot();s['billing']='metered'
        self.assertEqual(evaluate(s,'test',NOW)['status'],'NOT_APPLICABLE')

    def test_codex_auth_and_bucket(self):
        account={'account':{'type':'chatgpt','planType':'plus','email':'never-output@example.com'}}
        limits={'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':40,'windowDurationMins':300,'resetsAt':NOW+3600}}}}
        s=normalize(account,limits,'test',True,NOW)
        self.assertEqual(s['windows'][0]['remaining_percent'],60)
        self.assertNotIn('email',json.dumps(s))
        self.assertEqual(evaluate(s,'test',NOW)['status'],'READY')
        limits['rateLimitsByLimitId']['other']=limits['rateLimitsByLimitId'].pop('codex')
        self.assertEqual(normalize(account,limits,'test',True,NOW)['windows'],[])
        self.assertEqual(normalize({'account':{'type':'chatgpt','planType':'free'}},{},'test',True,NOW)['billing'],'unknown')

    def test_zcode_native_semantics(self):
        e={'adapter':'zcode-entitlement','route':'test','scope_verified':True,'observed_at':NOW,
            'current_provider':'zai-coding','native':{'generatedAt':NOW*1000,'provider':{'id':'zai-coding'},
            'subscription':{'plan':'active'},'quota':{'limits':[
                {'type':'TIME_LIMIT','percentage':99},
                {'type':'TOKENS_LIMIT','unit':3,'number':5,'percentage':40,'nextResetTime':(NOW+3600)*1000},
                {'type':'CREDIT_LIMIT','unit':6,'percentage':30,'nextResetTime':(NOW+80*3600)*1000}]}}}
        s=convert(e)
        self.assertEqual([w['remaining_percent'] for w in s['windows']],[60,70])
        self.assertEqual(evaluate(s,'test',NOW)['status'],'READY')
        e['native']['generatedAt']=(NOW-600)*1000
        self.assertEqual(evaluate(convert(e),'test',NOW)['status'],'UNKNOWN')
        e['current_provider']='different'
        self.assertFalse(convert(e)['scope_verified'])

    def test_dsh_wallet_and_provider_match(self):
        e={'adapter':'dsh-account-balance','route':'test','scope_verified':True,'observed_at':NOW,
           'current_provider':'deepseek-account','native':{'status':'ready','value':[{'currency':'USD','balance':'10'}]}}
        self.assertEqual(evaluate(convert(e),'test',NOW)['status'],'NOT_APPLICABLE')
        e['current_provider']='subscription-plugin'
        self.assertEqual(convert(e)['billing'],'unknown')

    def test_install_relocates_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            cmd=[sys.executable,str(ROOT/'install.py'),'--dest',d]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertTrue((Path(d)/'subscription-quota/scripts/budget.py').exists())
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)

if __name__ == '__main__':unittest.main()
