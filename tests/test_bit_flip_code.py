"""The code itself: does every single error give the syndrome the table expects?
Author: Swayam Shakya"""
import pytest
from qiskit_aer import AerSimulator

from bit_flip_code import BitFlipCode
import experiment_2_2_logical_error as exp22


@pytest.mark.parametrize('logical', ['0', '1'])
@pytest.mark.parametrize('flipped', [None, 0, 1, 2])
def test_noiseless_syndrome_points_at_the_flipped_qubit(logical, flipped):
    code = BitFlipCode(seed=0)
    qc = code.encode(logical)
    if flipped is not None:
        code.inject_error(qc, flipped)
    qc = code.syndrome_circuit(qc)
    counts = AerSimulator(seed_simulator=1).run(qc, shots=64).result().get_counts()
    assert len(counts) == 1, 'without noise the syndrome must be deterministic'
    syndrome = next(iter(counts))
    assert code.decode_syndrome(syndrome) == flipped


def test_table_covers_all_four_syndromes():
    assert set(BitFlipCode.SYNDROME_TABLE) == {'00', '01', '10', '11'}
    assert sorted(q for q in BitFlipCode.SYNDROME_TABLE.values() if q is not None) == [0, 1, 2]


def test_bad_inputs_are_rejected():
    code = BitFlipCode()
    with pytest.raises(ValueError):
        code.encode('+')
    with pytest.raises(ValueError):
        code.inject_error(code.encode('0'), 3)


def test_noisy_cycle_returns_sensible_values():
    code = BitFlipCode(seed=3)
    syndrome, correction, latency_ns, ok = code.run_cycle('1', 2)
    assert syndrome in BitFlipCode.SYNDROME_TABLE
    assert latency_ns >= 0
    assert ok == (correction == 2)


def test_feedforward_circuit_fixes_every_single_flip():
    """With p = 0 the real-time circuit must always return |111>."""
    sim = AerSimulator(noise_model=exp22.noise(0.0), seed_simulator=5)
    counts = sim.run(exp22.encoded_circuit(), shots=200).result().get_counts()
    assert exp22.failures(counts) == 0


def test_logical_error_formula():
    for p in (0.0, 0.01, 0.1, 0.5):
        assert 3 * p**2 * (1 - p) + p**3 == pytest.approx(3 * p**2 - 2 * p**3)
    assert 3 * 0.5**2 - 2 * 0.5**3 == pytest.approx(0.5)     # break-even at p = 1/2
