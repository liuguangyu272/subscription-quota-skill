"""Synthetic cases only; never export these as live account evidence."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skill/subscription-quota/scripts'))
from budget import evaluate
for name,remaining,hours,duration in [('five-hour-tight',10,2,5),('five-hour-near-reset',10,.25,5),('weekly-even',50,84,168)]:
    s={'schema_version':1,'route':'simulation','scope_verified':True,'observed_at':1000,
       'billing':'subscription','evidence':{'source':'SYNTHETIC'},'windows':[
       {'id':'demo','remaining_percent':remaining,'window_hours':duration,'resets_at':1000+hours*3600}]}
    print(json.dumps({'case':name,'result':evaluate(s,'simulation',1000)},indent=2))
