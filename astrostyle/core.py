"""Width-proportional rcParams engine with project-wide style defaults."""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import Literal

import matplotlib as mpl

from .latex import detect_tex_support

# Column widths (inches) that fit ApJ/AJ, MNRAS, A&A and Nature Astronomy within ~4%.
SINGLE_COL: float = 3.50
DOUBLE_COL: float = 7.10

DEFAULT_FRAME_WEIGHT: float = 2.4
DEFAULT_TEXT_SCALE: float = 1.0

# Colorblind-safe discrete palettes.
PALETTES: dict[str, list[str]] = {
    "okabe_ito": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#111111"],
    "tol_bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#333333"],
    "astro_high_contrast": ["#0B5FFF", "#C23B75", "#00876C", "#D95F02", "#7570B3", "#1A1A1A"],
}

DARK_CMAP_NAMES: set[str] = {
    "inferno", "magma", "plasma", "viridis", "cividis",
    "gray", "grey", "gist_heat", "afmhot", "cubehelix", "twilight_shifted",
}

ContextName = Literal["paper", "talk", "poster"]
UseTexMode = Literal["auto", True, False]

STYLE_KEYS = ("frame_weight", "text_scale", "context", "usetex", "palette")

_project_style: dict[str, object] = {
    "frame_weight": DEFAULT_FRAME_WEIGHT,
    "text_scale": DEFAULT_TEXT_SCALE,
    "context": "paper",
    "usetex": "auto",
    "palette": "okabe_ito",
}


def compute_style_metrics(
    width: float = SINGLE_COL,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
) -> dict[str, float]:
    """
    Font sizes, frame, tick and line weights for a figure `width` inches wide.

    Text grows sub-linearly with width (~1.37x from SINGLE_COL to DOUBLE_COL);
    `frame_weight` is reached exactly at DOUBLE_COL.
    """
    ctx = {"paper": 1.0, "talk": 1.25, "poster": 1.45}.get(context, 1.0)
    ts = max(width / SINGLE_COL, 0.75) ** 0.45 * text_scale * ctx
    fw = frame_weight * (max(width, 2.5) / DOUBLE_COL) ** 0.28 * ctx

    return {
        "font_size": round(12.5 * ts, 2),
        "title_size": round(14.5 * ts, 2),
        "label_size": round(14.0 * ts, 2),
        "tick_label_size": round(12.0 * ts, 2),
        "legend_size": round(12.5 * ts, 2),
        "label_pad": round(6.0 * ts, 2),
        "tick_pad": round(5.5 * ts, 2),
        "axes_linewidth": round(fw, 2),
        "major_tick_size": round(3.4 * fw, 2),
        "minor_tick_size": round(1.85 * fw, 2),
        "major_tick_width": round(0.95 * fw, 2),
        "minor_tick_width": round(0.70 * fw, 2),
        "line_width": round(1.22 * fw, 2),
        "marker_size": round(2.8 * fw, 2),
    }


def _resolve_tex(usetex: UseTexMode) -> tuple[bool, str]:
    if usetex == "auto":
        return detect_tex_support()
    if not usetex:
        return False, ""
    available, preamble = detect_tex_support()
    if not available:
        warnings.warn(
            "usetex=True requested but the latex/dvipng probe failed; saving may raise.",
            RuntimeWarning,
            stacklevel=3,
        )
    return True, preamble or r"\usepackage{amsmath,amssymb,bm}"


def _set_rcparams(width, frame_weight, text_scale, context, usetex, palette) -> None:
    m = compute_style_metrics(width, frame_weight, text_scale, context)
    tex_enabled, preamble = _resolve_tex(usetex)
    ink = "#111111"

    mpl.rcParams.update({
        "figure.figsize": (width, round(width * 0.78, 3)),
        "figure.dpi": 150,
        "figure.constrained_layout.use": True,

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

        "font.size": m["font_size"],
        "axes.titlesize": m["title_size"],
        "axes.titleweight": "bold",
        "axes.labelsize": m["label_size"],
        "axes.labelweight": "bold",
        "axes.labelpad": m["label_pad"],
        "xtick.labelsize": m["tick_label_size"],
        "ytick.labelsize": m["tick_label_size"],
        "legend.fontsize": m["legend_size"],

        "axes.linewidth": m["axes_linewidth"],
        "axes.edgecolor": ink,
        "axes.labelcolor": ink,
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
        "xtick.color": ink,
        "ytick.color": ink,

        "lines.linewidth": m["line_width"],
        "lines.markersize": m["marker_size"],
        "errorbar.capsize": 0,
        "patch.linewidth": m["axes_linewidth"] * 0.8,
        "axes.prop_cycle": mpl.cycler(color=PALETTES.get(palette, PALETTES["okabe_ito"])),
        "image.cmap": "inferno",
        "image.origin": "lower",

        "legend.frameon": False,
        "legend.handlelength": 2.0,
        "legend.handletextpad": 0.65,
        "legend.labelspacing": 0.45,
        "legend.borderaxespad": 0.6,

        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.08,
        "savefig.facecolor": "white",
    })


def apply_style(
    width: float = SINGLE_COL,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "okabe_ito",
) -> None:
    """
    Set the project-wide style and apply it to Matplotlib's rcParams.

    Every `fig_*` builder afterwards inherits these settings (only `width` is
    per-figure), so call this once at the top of a project to switch e.g. to
    `context="talk"` or another palette. Use it directly before hand-built
    layouts (GridSpec, seaborn) that bypass the builders.

    usetex: "auto" uses LaTeX when latex + dvipng work and falls back to STIX
    mathtext otherwise; True forces LaTeX; False always uses mathtext.
    palette: a key of PALETTES.
    """
    _project_style.update(
        frame_weight=frame_weight, text_scale=text_scale, context=context, usetex=usetex, palette=palette
    )
    _set_rcparams(width, **_project_style)


def figure_style(width: float, kwargs: dict, text_mult: float = 1.0) -> dict[str, object]:
    """Apply the project style for one figure, popping per-figure overrides out of `kwargs`."""
    style = {**_project_style, **{k: kwargs.pop(k) for k in STYLE_KEYS if k in kwargs}}
    style["text_scale"] *= text_mult
    _set_rcparams(width, **style)
    return style


@contextmanager
def style_context(**kwargs):
    """Apply astrostyle inside a `with` block, restoring rcParams and project style afterwards."""
    prev_rc = mpl.rcParams.copy()
    prev_style = dict(_project_style)
    try:
        apply_style(**kwargs)
        yield
    finally:
        mpl.rcParams.update(prev_rc)
        _project_style.clear()
        _project_style.update(prev_style)
