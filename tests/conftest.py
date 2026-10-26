"""Shared test setup: make src/ importable and run each test in a scratch folder
so nothing gets written into the repository. Author: Swayam Shakya"""
import os
import sys

import pytest

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'src')
sys.path.insert(0, os.path.abspath(SRC))


@pytest.fixture(autouse=True)
def _scratch_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
