"""The notebook is the main record of the project, so it gets checked too:
valid format, no stored errors, and it uses the same code as everything else.
(Executing it takes about five minutes; the CI 'notebook' job does that.)
Author: Swayam Shakya"""
import json
import os
import re

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
NB = os.path.join(ROOT, 'QEC_Latency_Decoder.ipynb')


@pytest.fixture(scope='module')
def nb():
    with open(NB, encoding='utf-8') as fh:
        return json.load(fh)


def code_cells(nb):
    return [c for c in nb['cells'] if c['cell_type'] == 'code']


def test_notebook_is_valid_nbformat_4(nb):
    assert nb['nbformat'] == 4
    assert nb['metadata']['kernelspec']['language'] == 'python'
    for cell in nb['cells']:
        assert cell['cell_type'] in ('markdown', 'code')


def test_no_stored_error_outputs(nb):
    for cell in code_cells(nb):
        for out in cell.get('outputs', []):
            assert out['output_type'] != 'error', out.get('evalue')


def test_cells_were_run_top_to_bottom(nb):
    counts = [c['execution_count'] for c in code_cells(nb)]
    if any(counts):                      # a stored, executed copy must have run in order
        assert counts == list(range(1, len(counts) + 1))


def test_notebook_runs_the_repository_code(nb):
    source = '\n'.join(''.join(c['source']) for c in code_cells(nb))
    for module in ('experiment_1_1_coherence', 'experiment_1_2_pauli_sensitivity', 'bit_flip_code',
                   'experiment_2_2_logical_error', 'fit_distribution', 'experiment_3_jitter_profiler',
                   'analysis_paper_ready', 'experiment_4_real_hardware'):
        assert f'import {module}' in source
        assert os.path.exists(os.path.join(ROOT, 'src', module + '.py'))
    assert 'RERUN = True' in source      # the committed copy reruns everything by default


def test_every_citation_has_a_reference(nb):
    text = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'markdown')
    cited = {int(n) for n in re.findall(r'\]\(#ref-(\d+)\)', text)}
    listed = {int(n) for n in re.findall(r'<a id="ref-(\d+)"></a>', text)}
    assert cited and cited == listed == set(range(1, len(listed) + 1))
