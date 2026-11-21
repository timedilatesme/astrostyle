"""Dynamic, width-proportional astrophysics plotting style engine."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Literal

import matplotlib as mpl

from .latex import detect_tex_support

# Universal column widths (inches) across ApJ/AJ/ApJS, MNRAS, A&A, Nature Astronomy.
# Dropping these PDFs into any major astro journal scales them by <= +/-4%.
SINGLE_COL: float = 3.50   # ~88.9 mm
DOUBLE_COL: float = 7.10   # ~180.3 mm

# Confirmed default visual parameters (heavy bold frames + prominent inward ticks + large text).
DEFAULT_FRAME_WEIGHT: float = 2.4
DEFAULT_TEXT_SCALE: float = 1.0

# Curated colorblind-safe discrete palettes (high contrast in color & grayscale print).
PALETTES: dict[str, list[str]] = {
    "okabe_ito": [
        "#0072B2",  # Deep blue
        "#D55E00",  # Vermilion
        "#009E73",  # Bluish green
        "#CC79A7",  # Reddish purple
        "#E69F00",  # Amber
        "#56B4E9",  # Sky blue
        "#111111",  # Near-black
    ],
    "tol_bright": [
        "#4477AA",
        "#EE6677",
        "#228833",
        "#CCBB44",
        "#66CCEE",
        "#AA3377",
        "#333333",
    ],
    "astro_high_contrast": [
        "#0B5FFF",  # Vibrant cobalt
        "#C23B75",  # Deep magenta-rose
        "#00876C",  # Deep teal
        "#D95F02",  # Burnt orange
        "#7570B3",  # Slate violet
        "#1A1A1A",  # Charcoal
    ],
}

COLORMAPS: dict[str, str] = {
    "intensity": "inferno",
    "density": "magma",
    "probability": "viridis",
    "velocity": "RdBu_r",
    "residual": "coolwarm",
}

DARK_CMAP_NAMES: set[str] = {
    "inferno", "magma", "plasma", "viridis", "cividis",
    "gray", "grey", "gist_heat", "afmhot", "cubehelix", "twilight_shifted",
}

ContextName = Literal["paper", "talk", "poster"]
UseTexMode = Literal["auto", True, False]

_ACTIVE_CONFIG: dict[str, object] = {
    "width": SINGLE_COL,
    "frame_weight": DEFAULT_FRAME_WEIGHT,
    "text_scale": DEFAULT_TEXT_SCALE,
    "context": "paper",
    "usetex": False,
    "palette": "okabe_ito",
}


def compute_style_metrics(
    width: float = SINGLE_COL,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
) -> dict[str, float]:
    """
    Compute width-proportional typography, border, tick, and curve weights.

    Anchors the confirmed 2.4 pt frame & tick weight at DOUBLE_COL (7.10 in) and scales
    smoothly across arbitrary widths so both single-column plots (3.5 in) and wide
    multi-panel or corner plots (7.1 in) stay visually balanced and authoritative.
    """
    ctx_mult = {"paper": 1.0, "talk": 1.25, "poster": 1.45}.get(context, 1.0)

    # Smooth sub-linear width scaling: 1.0x at 3.50 in -> ~1.37x at 7.10 in
    w_scale = max(width / SINGLE_COL, 0.75) ** 0.45
    ts = w_scale * text_scale * ctx_mult

    # Anchor frame_weight at DOUBLE_COL (7.10 in): 2.4 pt at double-col, ~1.95 pt at single-col
    fw_anchor = (max(width, 2.5) / DOUBLE_COL) ** 0.28
    fw = frame_weight * fw_anchor * ctx_mult

    return {
        "w_scale": w_scale,
        "text_scale_eff": ts,
        "frame_weight_eff": fw,
        "font_size": round(12.5 * ts, 2),
        "title_size": round(14.5 * ts, 2),
        "label_size": round(14.0 * ts, 2),
        "tick_label_size": round(12.0 * ts, 2),
        "legend_size": round(12.5 * ts, 2),
        "label_pad": round(6.0 * ts, 2),
        "tick_pad": round(5.5 * ts, 2),
        "axes_linewidth": round(fw, 2),
        # Crisp, unmistakable inward major & minor ticks without corner collisions
        "major_tick_size": round(3.4 * fw, 2),
        "minor_tick_size": round(1.85 * fw, 2),
        "major_tick_width": round(0.95 * fw, 2),
        "minor_tick_width": round(0.70 * fw, 2),
        "line_width": round(1.22 * fw, 2),
        "marker_size": round(2.8 * fw, 2),
    }


def apply_style(
    width: float = SINGLE_COL,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "okabe_ito",
) -> dict[str, object]:
    """
    Configure Matplotlib rcParams dynamically for publication-grade astrophysics figures.

    Parameters
    ----------
    width : float
        Target figure width in inches (SINGLE_COL=3.50 or DOUBLE_COL=7.10).
    frame_weight : float
        Base border/tick weight in points (default 2.4 pt anchored at DOUBLE_COL).
    text_scale : float
        Global typography multiplier (default 1.0).
    context : {'paper', 'talk', 'poster'}
        Presentation scaling preset.
    usetex : {'auto', True, False}
        - 'auto': Use real LaTeX if latex + dvipng compile cleanly; else STIX mathtext.
        - True: Force real LaTeX.
        - False: Built-in STIX mathtext (fast, zero external TeX dependencies).
    palette : str
        Name of discrete palette in PALETTES ('okabe_ito', 'tol_bright', 'astro_high_contrast').
    """
    m = compute_style_metrics(
        width=width,
        frame_weight=frame_weight,
        text_scale=text_scale,
        context=context,
    )
    colors = PALETTES.get(palette, PALETTES["okabe_ito"])

    tex_enabled = False
    preamble = ""
    if usetex == "auto":
        tex_enabled, preamble = detect_tex_support()
    elif usetex is True:
        avail, detected_preamble = detect_tex_support()
        tex_enabled = True
        preamble = detected_preamble or r"\usepackage{amsmath,amssymb,bm}"
        if not avail:
            import warnings
            warnings.warn(
                "usetex=True was explicitly requested, but latex/dvipng probe failed. "
                "Matplotlib may raise an error when saving unless TeX is installed.",
                RuntimeWarning,
                stacklevel=2,
            )

    rc = {
        # Canvas & layout
        "figure.figsize": (width, round(width * 0.78, 3)),
        "figure.dpi": 150,
        "figure.constrained_layout.use": True,

        # Typography & LaTeX / STIX math
        "text.usetex": tex_enabled,
        "text.latex.preamble": preamble if tex_enabled else "",
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif", "Computer Modern Roman"],
        "mathtext.fontset": "stix",
        "mathtext.bf": "serif:bold",
        "mathtext.rm": "serif",
        "mathtext.it": "serif:italic",
        "axes.unicode_minus": True,
        "axes.formatter.use_mathtext": True,

        # Bold, commanding typography scaled to figure width
        "font.size": m["font_size"],
        "axes.titlesize": m["title_size"],
        "axes.titleweight": "bold",
        "axes.labelsize": m["label_size"],
        "axes.labelweight": "bold",
        "axes.labelpad": m["label_pad"],
        "xtick.labelsize": m["tick_label_size"],
        "ytick.labelsize": m["tick_label_size"],
        "legend.fontsize": m["legend_size"],

        # Thick enclosed frames & prominent INWARD major + minor ticks on all 4 sides
        "axes.linewidth": m["axes_linewidth"],
        "axes.edgecolor": "#111111",
        "axes.labelcolor": "#111111",
        "axes.grid": False,
        "xtick.top": True,
        "xtick.bottom": True,
        "ytick.left": True,
        "ytick.right": True,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "xtick.major.size": m["major_tick_size"],
        "ytick.major.size": m["major_tick_size"],
        "xtick.minor.size": m["minor_tick_size"],
        "ytick.minor.size": m["minor_tick_size"],
        "xtick.major.width": m["major_tick_width"],
        "ytick.major.width": m["major_tick_width"],
        "xtick.minor.width": m["minor_tick_width"],
        "ytick.minor.width": m["minor_tick_width"],
        "xtick.major.pad": m["tick_pad"],
        "ytick.major.pad": m["tick_pad"],
        "xtick.color": "#111111",
        "ytick.color": "#111111",

        # Curves, markers, errorbars, colormaps
        "lines.linewidth": m["line_width"],
        "lines.markersize": m["marker_size"],
        "errorbar.capsize": 0,
        "patch.linewidth": m["axes_linewidth"] * 0.8,
        "axes.prop_cycle": mpl.cycler(color=colors),
        "image.cmap": COLORMAPS["intensity"],
        "image.origin": "lower",

        # Clean unboxed legends
        "legend.frameon": False,
        "legend.handlelength": 2.0,
        "legend.handletextpad": 0.65,
        "legend.labelspacing": 0.45,
        "legend.borderaxespad": 0.6,

        # Editable vector PDFs + crisp PNG previews
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.08,
        "savefig.facecolor": "white",
    }

    mpl.rcParams.update(rc)

    _ACTIVE_CONFIG.update({
        "width": width,
        "frame_weight": frame_weight,
        "text_scale": text_scale,
        "context": context,
        "usetex": tex_enabled,
        "palette": palette,
        "metrics": m,
    })
    return dict(_ACTIVE_CONFIG)


def get_active_config() -> dict[str, object]:
    """Return a copy of the currently active astrostyle configuration."""
    return dict(_ACTIVE_CONFIG)


@contextmanager
def style_context(**kwargs):
    """Temporarily apply astrostyle inside a `with` block without mutating global rcParams."""
    prev = mpl.rcParams.copy()
    prev_cfg = dict(_ACTIVE_CONFIG)
    try:
        apply_style(**kwargs)
        yield
    finally:
        mpl.rcParams.update(prev)
        _ACTIVE_CONFIG.clear()
        _ACTIVE_CONFIG.update(prev_cfg)
