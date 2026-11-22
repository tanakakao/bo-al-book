"""Shared synthetic experiment and plotting convention for the chapter notebooks."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import torch
from matplotlib import font_manager
from robotorchan.models import SingleTaskGP

DTYPE = torch.float64
SEED = 2026
NOISE_SD = 2.0  # MPa
ROOT = Path(__file__).resolve().parent.parent
FIGURES = ROOT / "figures"
QUALITY = ROOT / "quality"

BLUE = "#17558b"
ORANGE = "#ae4e18"
GREEN = "#187766"
INK = "#192c3a"


def setup():
    """Use one CPU thread and the same chart style in each notebook."""
    torch.manual_seed(SEED)
    torch.set_num_threads(1)
    preferred_fonts = ("Noto Sans CJK JP", "Yu Gothic", "Hiragino Sans")
    font = next(
        (name for name in preferred_fonts if name in font_manager.fontManager.get_font_names()),
        None,
    )
    if font is None:
        raise RuntimeError("Install Noto Sans CJK JP for the Japanese chart labels.")
    mpl.rcParams.update(
        {
            "font.family": font,
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.labelcolor": INK,
            "grid.alpha": 0.22,
            "figure.dpi": 135,
            "svg.fonttype": "path",
            "pdf.fonttype": 3,
        }
    )


def material_strength(x):
    """Latent synthetic strength in MPa. Inputs use x = (T - 140 °C) / 40 °C."""
    return 70 + 12 * torch.sin(2 * torch.pi * x) + 4 * torch.cos(4 * torch.pi * x) + 5 * x


def observations():
    """Return normalized temperature, observed strength, and noise variance."""
    x = torch.tensor([[0.05], [0.25], [0.43], [0.62], [0.86], [0.96]], dtype=DTYPE)
    generator = torch.Generator().manual_seed(SEED)
    noise = NOISE_SD * torch.randn(x.shape, generator=generator, dtype=DTYPE)
    y = material_strength(x) + noise
    return x, y, torch.full_like(y, NOISE_SD**2)


def fit_material_gp(train_x, train_y, train_yvar):
    """Use the library's public exact-GP training method."""
    model = SingleTaskGP(train_X=train_x, train_Y=train_y, train_Yvar=train_yvar)
    model.fit()
    model.eval()
    return model


def save_figure(fig, stem):
    """Save the same figure for HTML and PDF, then display it in Jupyter."""
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    plt.show()
    plt.close(fig)
