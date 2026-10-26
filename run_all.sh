#!/usr/bin/env bash
# run_all.sh - rerun every experiment and rebuild every figure (about 6 minutes)
# Author: Swayam Shakya
#
# Everything lands in outputs/, so the committed reference_results/ stay
# untouched and you can diff your run against mine.
set -euo pipefail
cd "$(dirname "$0")"
source qec-env/bin/activate

mkdir -p build outputs
gcc -O2 -shared -fPIC -o build/qec_decode.so src/qec_decode.c
export QEC_DECODE_LIB="$PWD/build/qec_decode.so"

cd outputs
python ../src/experiment_1_1_coherence.py
python ../src/experiment_1_2_pauli_sensitivity.py
python ../src/bit_flip_code.py
python ../src/experiment_2_2_logical_error.py
python ../src/fit_distribution.py

python ../src/experiment_3_jitter_profiler.py
python ../src/experiment_3_jitter_profiler.py --repeats 10
python ../src/analysis_paper_ready.py

python ../src/experiment_4_real_hardware.py draw
for dev in FakeKingston FakeSherbrooke; do
    python ../src/experiment_4_real_hardware.py local "$dev"
    python ../src/experiment_4_real_hardware.py sweep "$dev"
done
echo "All experiments finished. Results are in outputs/"
