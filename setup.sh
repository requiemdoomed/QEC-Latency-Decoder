#!/usr/bin/env bash
# setup.sh - one-time setup on Linux, macOS or WSL (Windows)
# Author: Swayam Shakya
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv qec-env              # Python 3.11, 3.12 or 3.13
source qec-env/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt  # the pinned stack plus pytest
pip check

python -c "import qiskit, qiskit_aer, qiskit_ibm_runtime as r; print('qiskit', qiskit.__version__, '| aer', qiskit_aer.__version__, '| runtime', r.__version__)"
gcc --version | head -n 1            # Weekend 3 needs a C compiler for the C decoder
echo "Setup done. Next: bash run_all.sh"
