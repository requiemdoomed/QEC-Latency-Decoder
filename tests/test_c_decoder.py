"""The C decoder must agree with the Python table, and its timers must work.
Author: Swayam Shakya"""
import ctypes
import os
import shutil
import subprocess

import numpy as np
import pytest

import experiment_3_jitter_profiler as prof

SRC_C = os.path.join(os.path.dirname(os.path.abspath(prof.__file__)), 'qec_decode.c')


@pytest.fixture(scope='module')
def lib(tmp_path_factory):
    if shutil.which('gcc') is None:
        pytest.skip('gcc is not installed')
    so = tmp_path_factory.mktemp('build') / 'qec_decode.so'
    # build with the strictest flags I could think of: warnings are errors
    subprocess.run(['gcc', '-O2', '-shared', '-fPIC', '-std=c11', '-Wall', '-Wextra',
                    '-Werror', '-o', str(so), SRC_C], check=True)
    return prof.load_c_library(str(so))


def test_c_table_matches_python_table(lib):
    lib.decode_syndrome.argtypes = [ctypes.c_uint8]
    lib.decode_syndrome.restype = ctypes.c_int8
    # the C side packs the string 'ab' as the integer 0bab
    for syndrome, qubit in prof.SYNDROME_TABLE.items():
        expected = -1 if qubit is None else qubit
        assert lib.decode_syndrome(int(syndrome, 2)) == expected


def test_batch_timers_return_positive_latencies(lib):
    n = 500
    lat = prof.c_tier(lib, n)
    floor = prof.c_floor(lib, n)
    assert lat.shape == (n,) and floor.shape == (n,)
    assert np.all(lat >= 0) and np.all(floor >= 0)
    assert np.median(lat) < 1e6        # a table lookup should never take a millisecond


def test_missing_library_gives_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv('QEC_DECODE_LIB', str(tmp_path / 'nope.so'))
    monkeypatch.setattr(prof.os.path, 'exists', lambda p: False)
    with pytest.raises(FileNotFoundError, match='gcc -O2'):
        prof.find_c_library()
