import subprocess,sys,runpy,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
from hybrid_kernel.core import Kernel,Refused
from hybrid_kernel.model import detached
from tcb.canon import digest
source=subprocess.check_output(['git','show','982dc3f236f161122ff588a19bc276a14367e186:tcb/kernel.py'],cwd=root,text=True)
source=source.replace('assert set(SHAPES) == set(POLARITY)', 'assert set(SHAPES) <= set(POLARITY)')
namespace={'__name__':'tcb.frozen_reference','__package__':'tcb'}
exec(compile(source,'frozen-reference-kernel.py','exec'),namespace)
Reference=namespace['Kernel'];OldRefused=namespace['Refused']
reference=Reference()
original=Kernel.decide
stats={'accepted_identical':0,'refused_identical':0,'new_stricter':[],'mismatch':[],'fault_injection_checks':0}

def compared(self,state,entry):
 # The adversarial suites deliberately replace instance handlers to verify
 # AND-checker rejection. These are not candidate-equivalence comparisons.
 if any(callable(value) for key,value in self.__dict__.items() if key not in ('code_pin','_laws','_local')):
  stats['fault_injection_checks']+=1
  return original(self,state,entry)
 try:
  new=original(self,state,entry);new_error=None
 except Refused as e:
  new=None;new_error=e
 try:
  old=reference.decide(state,entry);old_error=None
 except OldRefused as e:
  old=None;old_error=e
 if new_error:
  if old_error and new_error.code==old_error.code:
   stats['refused_identical']+=1
  elif old_error is None:
   stats['new_stricter'].append(new_error.code)
  else:
   stats['mismatch'].append({'new':new_error.code,'old':old_error.code})
  raise new_error
 if old_error:
  stats['mismatch'].append({'new':'ACCEPT','old':old_error.code})
 elif digest(detached(new))!=digest(detached(old)):
  stats['mismatch'].append({'new':'delta','old':'different_delta'})
 else:
  stats['accepted_identical']+=1
 return new
Kernel.decide=compared
suites=['test_kernel','test_effects','test_language','test_root_causes','test_v6','test_review']
failures=[]
for name in suites:
 try:
  runpy.run_path(str(root/'tests'/f'{name}.py'),run_name='__main__')
 except BaseException as e:
  failures.append({'suite':name,'failure':str(e)});traceback.print_exc()
result={'reference_commit':'982dc3f236f161122ff588a19bc276a14367e186',
        'scope':'Differential signed transition engine with shared release-law/crypto primitives; native extensions are separately tested. Frozen interpreter is test-only and never installed into runtime.',
        'suites':suites,**stats,'suite_failures':failures}
Path('/tmp/standard-differential.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
if stats['mismatch'] or failures:sys.exit(1)
