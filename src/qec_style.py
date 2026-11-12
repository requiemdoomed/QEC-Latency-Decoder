"""
qec_style.py - one place for the look of every figure in this project.
Author: Swayam Shakya

I got tired of every script having slightly different fonts and colours,
so they all import this first:

    import qec_style
    qec_style.apply()
    ...
    qec_style.save(fig, 'fig1_coherence_decay')

The three series colours (blue, orange, aqua) stay tell-apart-able for the
common kinds of colour blindness. Reference lines (deadlines, thresholds) are
always drawn in neutral ink so they never get confused with a data series.
"""
import matplotlib

matplotlib.use('Agg')            # no window needed, so this also works on a server / in CI
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'   # data series 1, 2, 3
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#d9d8d4'     # text, reference lines, grid


def apply() -> None:
    """Quiet axes, thin lines, and fonts embedded in the PDFs."""
    plt.rcParams.update({
        'figure.dpi': 110,
        'savefig.dpi': 300,
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'axes.edgecolor': MUTED,
        'axes.labelcolor': INK,
        'axes.titlecolor': INK,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.color': GRID,
        'grid.linewidth': 0.6,
        'xtick.color': MUTED,
        'ytick.color': MUTED,
        'lines.linewidth': 2.0,
        'legend.frameon': False,
        'pdf.fonttype': 42,      # TrueType fonts inside the PDF (journals ask for this)
    })


def save(fig, stem: str) -> None:
    """Write a vector PDF and a PNG preview with the same name, then free the figure."""
    fig.savefig(f'{stem}.pdf', bbox_inches='tight')
    fig.savefig(f'{stem}.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {stem}.pdf / {stem}.png')
