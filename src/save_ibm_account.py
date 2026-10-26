"""
save_ibm_account.py - run this once before the Weekend 4 hardware runs.
Author: Swayam Shakya

1. Sign in at https://quantum.cloud.ibm.com and create an API key.
2. Run:  python src/save_ibm_account.py
   and paste the key when asked (or set IBM_QUANTUM_TOKEN beforehand).

I ask for the key at run time on purpose, so it never ends up pasted into a
file that could get committed to GitHub by accident.

Note: the old 'ibm_quantum' channel was removed in qiskit-ibm-runtime 0.41;
the channel is now 'ibm_quantum_platform'.
"""
import os
from getpass import getpass

from qiskit_ibm_runtime import QiskitRuntimeService

token = os.environ.get('IBM_QUANTUM_TOKEN') or getpass('IBM Quantum API key: ').strip()
if not token:
    raise SystemExit('No API key given, nothing saved.')

QiskitRuntimeService.save_account(
    channel='ibm_quantum_platform',
    token=token,
    instance=os.environ.get('IBM_QUANTUM_INSTANCE'),   # optional: instance CRN or name
    set_as_default=True,
    overwrite=True,
)
print('Account saved. The Weekend 4 script will pick it up with QiskitRuntimeService().')
