"""Universal post-processor, visual linter, and dual-format exporter."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PathCollection, QuadMesh
from matplotlib.ticker import AutoMinorLocator, LogLocator, ScalarFormatter

from .core import DARK_CMAP_NAMES
from .latex import escape_tex_outside_math, lint_latex_text

RASTERIZE_POINT_THRESHOLD = 3000


def _is_colorbar_axis(ax: mpl.axes.Axes) -> bool:
    return ax.get_label() == "<colorbar>" or getattr(ax, "_is_astro_colorbar", False)


def _is_wcs_axis(ax: mpl.axes.Axes) -> bool:
    return hasattr(ax, "coords") and ax.__class__.__name__.startswith("WCSAxes")


def _has_dark_image(ax: mpl.axes.Axes) -> bool:
    mappables = list(ax.images) + [c for c in ax.collections if isinstance(c, QuadMesh)]
    if not mappables:
        return False
    cmap_name = mappables[0].get_cmap().name.lower()
    if cmap_name.endswith("_r"):
        return False
    return any(name in cmap_name for name in DARK_CMAP_NAMES)


def _auto_rasterize_heavy_artists(ax: mpl.axes.Axes, threshold: int = RASTERIZE_POINT_THRESHOLD) -> int:
    """Rasterize dense scatter/mesh layers so vector PDFs stay compact while text stays vector."""
    count = 0
    for coll in ax.collections:
        if coll.get_rasterized():
            continue
        if isinstance(coll, PathCollection):
            offsets = coll.get_offsets()
            if len(offsets) >= threshold:
                coll.set_rasterized(True)
                count += 1
        elif isinstance(coll, QuadMesh):
            arr = coll.get_array()
            if arr is not None and arr.size >= threshold:
                coll.set_rasterized(True)
                count += 1
    return count


def _enforce_minor_and_inward_ticks(ax: mpl.axes.Axes) -> None:
    """Guarantee thick borders and inward major + minor ticks on all four sides."""
    lw = mpl.rcParams["axes.linewidth"]
    for spine in ax.spines.values():
        spine.set_linewidth(lw)

    if _is_wcs_axis(ax):
        for coord in ax.coords:
            coord.set_ticks_position("all")
            coord.set_ticklabel_position("bl")
            coord.display_minor_ticks(True)
            coord.set_ticks(
                direction="in",
                size=mpl.rcParams["xtick.major.size"],
                width=mpl.rcParams["xtick.major.width"],
            )
        return

    if _is_colorbar_axis(ax):
        ax.tick_params(
            which="both",
            direction="in",
            size=mpl.rcParams["ytick.major.size"] * 0.75,
            width=mpl.rcParams["ytick.major.width"],
            labelsize=mpl.rcParams["ytick.labelsize"],
        )
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(
            which="minor",
            direction="in",
            size=mpl.rcParams["ytick.minor.size"] * 0.75,
            width=mpl.rcParams["ytick.minor.width"],
        )
        return

    is_marginal = getattr(ax, "_is_astro_marginal", False)

    axes_to_tick = (ax.xaxis,) if is_marginal else (ax.xaxis, ax.yaxis)
    for axis in axes_to_tick:
        scale = axis.get_scale()
        if scale == "log":
            axis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=12))
        elif scale == "linear":
            axis.set_minor_locator(AutoMinorLocator())
            fmt = axis.get_major_formatter()
            if isinstance(fmt, ScalarFormatter):
                fmt.set_useMathText(True)

    if is_marginal:
        ax.tick_params(axis="x", which="both", direction="in", top=False, bottom=True)
        ax.tick_params(axis="y", which="both", left=False, right=False, labelleft=False, labelright=False)
    else:
        ax.tick_params(axis="both", which="both", direction="in", top=True, bottom=True, left=True, right=True)

    if getattr(ax, "_auto_tick_contrast", True) and _has_dark_image(ax):
        ax.tick_params(which="both", colors="white", labelcolor="#111111")


def _sanitize_usetex_text(fig: mpl.figure.Figure) -> None:
    """When text.usetex=True, safely escape stray %, &, # outside math spans to prevent crashes."""
    if not mpl.rcParams.get("text.usetex", False):
        return
    for ax in fig.axes:
        if not ax.get_visible():
            continue
        ax.set_xlabel(escape_tex_outside_math(ax.get_xlabel()))
        ax.set_ylabel(escape_tex_outside_math(ax.get_ylabel()))
        if ax.get_title():
            ax.set_title(escape_tex_outside_math(ax.get_title()))
        leg = ax.get_legend()
        if leg is not None:
            for txt in leg.get_texts():
                txt.set_text(escape_tex_outside_math(txt.get_text()))
    for leg in fig.legends:
        for txt in leg.get_texts():
            txt.set_text(escape_tex_outside_math(txt.get_text()))


def lint_fig(fig: mpl.figure.Figure, verbose: bool = True) -> list[str]:
    """
    Inspect a rendered figure for visual & LaTeX defects:
    - Overlapping x/y tick labels
    - Raw unformatted subscripts/superscripts outside LaTeX math mode
    - Unbalanced '$' or unescaped TeX characters
    """
    issues: list[str] = []
    usetex_on = bool(mpl.rcParams.get("text.usetex", False))

    for idx, ax in enumerate(fig.axes):
        if not ax.get_visible():
            continue
        for kind, text in (("xlabel", ax.get_xlabel()), ("ylabel", ax.get_ylabel()), ("title", ax.get_title())):
            for w in lint_latex_text(text, usetex_enabled=usetex_on):
                issues.append(f"[axis {idx} {kind}] {w}")

    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception as exc:
        issues.append(f"[render] Failed to draw canvas for layout inspection: {exc}")
        if verbose:
            for msg in issues:
                print(f"[astrostyle WARNING] {msg}")
        return issues

    for idx, ax in enumerate(fig.axes):
        if not ax.get_visible() or _is_colorbar_axis(ax) or _is_wcs_axis(ax):
            continue
        for axis_name, labels in (("x", ax.get_xticklabels()), ("y", ax.get_yticklabels())):
            boxes = []
            for t in labels:
                if t.get_visible() and t.get_text().strip():
                    bbox = t.get_window_extent(renderer)
                    if bbox.width > 0 and bbox.height > 0:
                        boxes.append((t.get_text(), bbox))
            for (t1, b1), (t2, b2) in zip(boxes, boxes[1:]):
                if b1.padded(-1.0).overlaps(b2.padded(-1.0)):
                    issues.append(
                        f"[axis {idx}] Overlapping {axis_name}-tick labels ({t1!r} & {t2!r}). "
                        "Use MaxNLocator(nbins=3, prune='both') or increase figure width."
                    )
                    break

    if verbose:
        for msg in issues:
            print(f"[astrostyle WARNING] {msg}")
    return issues


def _sync_attached_colorbars(fig: mpl.figure.Figure) -> None:
    """Align sibling colorbar axes to the exact post-aspect bounding box of their parent image axes."""
    attached = [ax for ax in fig.axes if getattr(ax, "_astro_parent_ax", None) is not None]
    if not attached:
        return
    try:
        fig.canvas.draw()
    except Exception:
        return
    for cax in attached:
        parent = cax._astro_parent_ax
        parent.apply_aspect()
        pos = parent.get_position(original=False)
        pad = getattr(cax, "_astro_cbar_pad", 0.04) * pos.width
        w = getattr(cax, "_astro_cbar_width", 0.055) * pos.width
        cax.set_aspect("auto")
        cax.set_position([pos.x1 + pad, pos.y0, w, pos.height])


def polish(
    fig: mpl.figure.Figure,
    align_labels: bool = True,
    rasterize_threshold: int = RASTERIZE_POINT_THRESHOLD,
    lint: bool = True,
    verbose: bool = True,
) -> list[str]:
    """
    Universal post-processor: call on ANY figure (from archetype helpers or raw Matplotlib)
    to enforce bold frames, inward major+minor ticks, dark-image tick contrast,
    LaTeX safety, auto-rasterization, label alignment, and collision linting.
    """
    _sync_attached_colorbars(fig)

    for ax in fig.axes:
        if not ax.get_visible():
            continue
        _enforce_minor_and_inward_ticks(ax)
        if rasterize_threshold > 0:
            _auto_rasterize_heavy_artists(ax, threshold=rasterize_threshold)

    _sanitize_usetex_text(fig)

    if align_labels:
        try:
            fig.align_labels()
        except Exception:
            pass

    if lint:
        return lint_fig(fig, verbose=verbose)
    return []


def save(
    fig: mpl.figure.Figure,
    path_no_ext: str | Path,
    formats: Iterable[str] = ("pdf", "png"),
    do_polish: bool = True,
    lint: bool = True,
    close: bool = False,
) -> list[Path]:
    """
    Polish, lint, and export a figure to vector PDF + 300 dpi PNG preview.

    Returns the list of written output Paths.
    """
    if do_polish:
        polish(fig, lint=lint, verbose=True)

    out = Path(path_no_ext)
    if out.suffix.lower() in {".pdf", ".png", ".svg", ".eps"}:
        out = out.with_suffix("")
    out.parent.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for ext in formats:
        ext_clean = ext.lstrip(".")
        target = out.with_suffix(f".{ext_clean}")
        fig.savefig(target)
        written.append(target)

    if close:
        plt.close(fig)
    return written
