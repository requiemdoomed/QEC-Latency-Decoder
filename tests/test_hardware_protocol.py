"""Weekend 4 checks on a calibrated replica (no IBM account needed).
Author: Swayam Shakya"""
import subprocess
import sys

import pytest
from qiskit_ibm_runtime.fake_provider import FakeKingston

import experiment_4_real_hardware as hw


@pytest.mark.parametrize('syn, data, fixed', [
    ('00', '111', '111'),
    ('10', '110', '111'),     # qubit 0 is the right-most character
    ('11', '101', '111'),
    ('01', '011', '111'),
])
def test_offline_decoder_flips_the_right_bit(syn, data, fixed):
    assert hw.decode_offline(syn, data) == fixed


def test_majority_vote():
    assert hw.majority_is_one('110') and hw.majority_is_one('111')
    assert not hw.majority_is_one('100')


@pytest.fixture(scope='module')
def job():
    return hw.build_job(FakeKingston())


def test_all_circuits_share_one_layout(job):
    isa, delay_s, stats = job
    assert stats['offline']['physical_qubits'] == stats['realtime']['physical_qubits']
    assert stats['bare']['physical_qubits'][0] in stats['offline']['physical_qubits']
    assert 0 < delay_s < 50e-6                 # encode + syndrome takes a few µs


def test_transpiled_circuits_use_native_gates_only(job):
    isa, _, stats = job
    assert stats['bare']['two_qubit_gates'] == 0
    assert stats['realtime']['two_qubit_gates'] >= 6     # 6 CNOTs, plus routing


def test_bad_command_line_exits_with_an_error():
    run = subprocess.run([sys.executable, hw.__file__, 'nonsense'],
                         capture_output=True, text=True)
    assert run.returncode != 0
    assert 'Usage' in run.stderr
