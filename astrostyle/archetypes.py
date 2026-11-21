"""Aspect-locked figure builders for common astrophysics plot types.

Every `fig_*` builder inherits the project style set by `apply_style()`. Pass
`frame_weight`, `text_scale`, `context`, `usetex` or `palette` to override it
for one figure; any other keyword arguments go to `plt.subplots`/`plt.figure`.
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib.util import find_spec

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

from .core import DOUBLE_COL, PALETTES, SINGLE_COL, figure_style
from .polish import style_wcs_coords


def _attach_colorbar_axes(fig, ax, pad: float, width: float) -> mpl.axes.Axes:
    """Sibling colorbar axes; polish() re-syncs it to ax's post-aspect box (inset_axes clips under tight bbox)."""
    pos = ax.get_position()
    cax = fig.add_axes([pos.x1 + pad * pos.width, pos.y0, width * pos.width, pos.height])
    cax._is_astro_colorbar = True
    cax._astro_parent_ax = ax
    cax._astro_cbar_pad = pad
    cax._astro_cbar_width = width
    return cax


def _axes_point(ax, frac: tuple[float, float]) -> tuple[float, float]:
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    return x0 + frac[0] * (x1 - x0), y0 + frac[1] * (y1 - y0)


def fig_xy(width: float = SINGLE_COL, aspect: float = 0.78, **kwargs):
    """Single panel for curves, SEDs, light curves, scaling relations, scatter/errorbars. Returns (fig, ax)."""
    figure_style(width, kwargs)
    return plt.subplots(figsize=(width, width * aspect), **kwargs)


def fig_residuals(
    width: float = SINGLE_COL,
    aspect: float = 1.05,
    height_ratios: tuple[float, float] = (3.0, 1.05),
    *,
    zero_line: bool = True,
    **kwargs,
):
    """Zero-gap data/model panel over a residual panel. Returns (fig, ax_main, ax_res)."""
    figure_style(width, kwargs)
    fig, (ax_main, ax_res) = plt.subplots(
        2, 1,
        figsize=(width, width * aspect),
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios, "hspace": 0.0},
        layout="none",
        **kwargs,
    )
    ax_main.tick_params(axis="x", labelbottom=False)
    ax_res.yaxis.set_major_locator(MaxNLocator(nbins=3, prune="upper"))
    if zero_line:
        ax_res.axhline(0.0, color="#444444", lw=mpl.rcParams["axes.linewidth"] * 0.65, ls="--", zorder=0)
    return fig, ax_main, ax_res


def fig_image(
    width: float = SINGLE_COL,
    aspect: float = 1.0,
    *,
    colorbar: bool = True,
    cbar_width: float = 0.055,
    cbar_pad: float = 0.035,
    dark_ticks: bool = False,
    **kwargs,
):
    """
    Square 2D map (image, FITS cutout, density) with a height-matched colorbar.

    Returns (fig, ax, cax), or (fig, ax) when colorbar=False. Ticks turn white
    over dark colormaps unless dark_ticks=True.
    """
    figure_style(width, kwargs)
    fig, ax = plt.subplots(figsize=(width, width * aspect), layout="none", **kwargs)
    ax.set_aspect("equal", adjustable="box")
    ax._auto_tick_contrast = not dark_ticks
    if not colorbar:
        return fig, ax
    return fig, ax, _attach_colorbar_axes(fig, ax, cbar_pad, cbar_width)


def fig_wcs(wcs, width: float = SINGLE_COL, aspect: float = 1.0, *, colorbar: bool = True, cbar_pad: float = 0.03, **kwargs):
    """Astropy WCS sky map with inward RA/Dec ticks. Returns (fig, ax, cax), or (fig, ax) when colorbar=False."""
    try:
        import astropy.visualization.wcsaxes  # noqa: F401
    except ImportError as exc:
        raise ImportError("fig_wcs() requires astropy: pip install 'astrostyle[wcs]'") from exc

    figure_style(width, kwargs)
    fig = plt.figure(figsize=(width * (1.20 if colorbar else 1.0), width * aspect), layout="none", **kwargs)
    ax = fig.add_subplot(111, projection=wcs)
    ax.set_aspect("equal", adjustable="box")
    style_wcs_coords(ax)
    if not colorbar:
        return fig, ax
    return fig, ax, _attach_colorbar_axes(fig, ax, cbar_pad, 0.055)


def fig_grid(nrows: int, ncols: int, width: float | None = None, aspect: float | None = None, *, tight_panels: bool = False, **kwargs):
    """Multi-panel grid; tight_panels=True gives shared, zero-gap axes. Returns (fig, axes)."""
    width = width or (SINGLE_COL if ncols == 1 else DOUBLE_COL)
    aspect = aspect or (0.78 * nrows / ncols)
    figure_style(width, kwargs, text_mult=0.90 if ncols >= 3 else 1.0)

    if tight_panels:
        kwargs.setdefault("sharex", True)
        kwargs.setdefault("sharey", True)
        kwargs["gridspec_kw"] = {"hspace": 0.0, "wspace": 0.0}
        kwargs["layout"] = "none"

    fig, axes = plt.subplots(nrows, ncols, figsize=(width, width * aspect), **kwargs)
    if tight_panels:
        for ax in np.atleast_1d(axes).flat:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4, prune="both"))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=4, prune="both"))
    return fig, axes


def label_panels(
    axes,
    labels: Sequence[str] | None = None,
    *,
    loc: str = "upper left",
    fmt: str = "({letter})",
    color: str = "#111111",
    fontsize: float | None = None,
) -> None:
    """Add bold (a), (b), ... labels inside a corner of each visible panel."""
    x, y, ha, va = {
        "upper left": (0.04, 0.94, "left", "top"),
        "upper right": (0.96, 0.94, "right", "top"),
        "lower left": (0.04, 0.06, "left", "bottom"),
        "lower right": (0.96, 0.06, "right", "bottom"),
    }[loc]
    flat = list(axes.flat) if hasattr(axes, "flat") else [axes]
    labels = labels or [fmt.format(letter=chr(97 + i)) for i in range(len(flat))]
    fs = fontsize or mpl.rcParams["axes.labelsize"]
    for ax, lab in zip(flat, labels):
        if ax.get_visible():
            ax.text(x, y, lab, transform=ax.transAxes, fontsize=fs, fontweight="bold", color=color, ha=ha, va=va)


def add_beam(
    ax: mpl.axes.Axes,
    bmaj: float,
    bmin: float,
    bpa: float = 0.0,
    *,
    loc: tuple[float, float] = (0.12, 0.12),
    edgecolor: str = "white",
    facecolor: str = "none",
    hatch: str | None = "////",
    linewidth: float | None = None,
) -> Ellipse:
    """Draw a beam/PSF ellipse (data units) centred at fractional axes position `loc`."""
    ell = Ellipse(
        _axes_point(ax, loc),
        width=bmin,
        height=bmaj,
        angle=-bpa,
        edgecolor=edgecolor,
        facecolor=facecolor,
        hatch=hatch,
        linewidth=linewidth or mpl.rcParams["axes.linewidth"] * 0.8,
        zorder=10,
    )
    ax.add_patch(ell)
    return ell


def add_scalebar(
    ax: mpl.axes.Axes,
    length: float,
    label: str,
    *,
    loc: tuple[float, float] = (0.66, 0.10),
    color: str = "white",
    linewidth: float | None = None,
) -> None:
    """Draw a labelled scale bar of `length` data units starting at fractional axes position `loc`."""
    x0, y0 = _axes_point(ax, loc)
    lw = linewidth or mpl.rcParams["axes.linewidth"] * 1.1
    ax.plot([x0, x0 + length], [y0, y0], color=color, lw=lw, solid_capstyle="butt", zorder=10)
    dy = 0.035 * np.ptp(ax.get_ylim())
    ax.text(
        x0 + 0.5 * length, y0 + dy, label,
        color=color, ha="center", va="bottom",
        fontsize=mpl.rcParams["xtick.labelsize"], fontweight="bold", zorder=10,
    )


def add_inset(
    ax: mpl.axes.Axes,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    *,
    width: str = "38%",
    height: str = "38%",
    loc: str = "upper right",
    connect: bool = True,
    loc1: int = 2,
    loc2: int = 4,
) -> mpl.axes.Axes:
    """Add a zoomed inset showing `xlim` x `ylim`, optionally connected to the zoom region."""
    axins = inset_axes(ax, width=width, height=height, loc=loc, borderpad=0.9)
    axins.set_xlim(*xlim)
    axins.set_ylim(*ylim)
    axins.xaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
    axins.yaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
    axins.tick_params(which="both", direction="in", top=True, right=True, labelsize=mpl.rcParams["xtick.labelsize"] * 0.85)
    if connect:
        mark_inset(ax, axins, loc1=loc1, loc2=loc2, fc="none", ec="#333333", lw=mpl.rcParams["axes.linewidth"] * 0.6)
    return axins


def _smooth(arr: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return arr
    try:
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(arr, sigma)
    except ImportError:
        for axis in range(arr.ndim):
            arr = np.apply_along_axis(np.convolve, axis, arr, [0.2, 0.6, 0.2], mode="same")
        return arr


def _credible_levels(hist2d: np.ndarray) -> tuple[float, float]:
    """Density thresholds enclosing 95% and 68% of the mass."""
    flat = np.sort(hist2d.ravel())[::-1]
    if flat.sum() <= 0:
        return 0.0, 0.0
    cdf = np.cumsum(flat) / flat.sum()
    lev95, lev68 = (float(flat[min(np.searchsorted(cdf, p), len(flat) - 1)]) for p in (0.95, 0.68))
    return lev95, lev68


def _plot_builtin_corner(fig, chains, labels, ranges, colors, truths, smooth, n_bins: int = 38) -> np.ndarray:
    """NumPy/Matplotlib-only corner plot, used when `corner` is unavailable."""
    n_dim = len(labels)
    axes = np.atleast_2d(fig.subplots(n_dim, n_dim))
    lw = mpl.rcParams["lines.linewidth"]

    for r in range(n_dim):
        for c in range(r + 1):
            ax = axes[r, c]
            if r == c:
                for i, samples in enumerate(chains):
                    color = colors[i % len(colors)]
                    counts, edges = np.histogram(samples[:, c], bins=n_bins, range=ranges[c], density=True)
                    centers = 0.5 * (edges[:-1] + edges[1:])
                    pdf = _smooth(counts, smooth)
                    pdf = pdf / pdf.max() if pdf.max() > 0 else pdf
                    ax.plot(centers, pdf, color=color, lw=lw)
                    ax.fill_between(centers, 0, pdf, color=color, alpha=0.18)
                if truths is not None:
                    ax.axvline(truths[c], color="#444444", ls="--", lw=lw * 0.7)
                ax.set_xlim(*ranges[c])
            else:
                for i, samples in enumerate(chains):
                    color = colors[i % len(colors)]
                    H, xe, ye = np.histogram2d(samples[:, c], samples[:, r], bins=n_bins, range=[ranges[c], ranges[r]])
                    Hs = _smooth(H.T, smooth)
                    xc, yc = 0.5 * (xe[:-1] + xe[1:]), 0.5 * (ye[:-1] + ye[1:])
                    lev95, lev68 = _credible_levels(Hs)
                    hmax = float(Hs.max()) * 1.01
                    if lev95 < lev68 < hmax:
                        ax.contourf(xc, yc, Hs, levels=[lev95, lev68, hmax], colors=[color, color], alpha=0.22)
                        ax.contourf(xc, yc, Hs, levels=[lev68, hmax], colors=[color], alpha=0.25)
                        ax.contour(xc, yc, Hs, levels=[lev95, lev68], colors=[color], linewidths=[lw * 0.8, lw])
                if truths is not None:
                    ax.axvline(truths[c], color="#444444", ls="--", lw=lw * 0.65)
                    ax.axhline(truths[r], color="#444444", ls="--", lw=lw * 0.65)
                ax.set_xlim(*ranges[c])
                ax.set_ylim(*ranges[r])

            if r == n_dim - 1:
                ax.set_xlabel(labels[c])
            else:
                ax.tick_params(axis="x", labelbottom=False)
            if c == 0 and r > 0:
                ax.set_ylabel(labels[r])
            elif r != c:
                ax.tick_params(axis="y", labelleft=False)
    return axes


def _plot_corner_pkg(fig, chains, labels, ranges, colors, truths, smooth, max_n_ticks) -> np.ndarray:
    import corner

    lw = mpl.rcParams["lines.linewidth"]
    for i, samples in enumerate(chains):
        color = colors[i % len(colors)]
        rgb = mpl.colors.to_rgb(color)
        corner.corner(
            samples,
            fig=fig,
            labels=list(labels),
            range=ranges,
            color=color,
            truths=truths if i == 0 else None,
            truth_color="#444444",
            levels=(0.68, 0.95),
            smooth=smooth,
            plot_datapoints=False,
            plot_density=False,
            fill_contours=True,
            contourf_kwargs={"colors": [(*rgb, 0.0), (*rgb, 0.16), (*rgb, 0.32)]},
            contour_kwargs={"linewidths": lw * 0.9},
            hist_kwargs={"density": True, "linewidth": lw},
            label_kwargs={"fontsize": mpl.rcParams["axes.labelsize"], "fontweight": "bold"},
            max_n_ticks=max_n_ticks,
            use_math_text=True,
        )
    n_dim = len(labels)
    return np.array(fig.axes).reshape((n_dim, n_dim))


def fig_corner(
    chains: np.ndarray | Sequence[np.ndarray],
    labels: Sequence[str],
    *,
    names: Sequence[str] | None = None,
    truths: Sequence[float] | None = None,
    ranges: Sequence[tuple[float, float]] | None = None,
    width: float | None = None,
    max_n_ticks: int = 3,
    smooth: float = 1.15,
    use_corner_pkg: bool = True,
    **kwargs,
):
    """
    Multi-chain posterior corner plot with square panels. Returns (fig, axes).

    Uses the `corner` package when installed (and use_corner_pkg=True), otherwise
    a built-in NumPy renderer. `names` adds a legend entry per chain.
    """
    chains = [np.asarray(chains)] if isinstance(chains, np.ndarray) else [np.asarray(c) for c in chains]
    n_dim = chains[0].shape[1]
    if len(labels) != n_dim:
        raise ValueError(f"Expected {n_dim} labels matching chain columns, got {len(labels)}.")

    width = width or (DOUBLE_COL if n_dim >= 3 else 4.6)
    style = figure_style(width, kwargs, text_mult=1.0 if n_dim <= 3 else max(0.78, 1.0 - 0.06 * (n_dim - 3)))
    colors = PALETTES.get(style["palette"], PALETTES["okabe_ito"])

    if ranges is None:
        ranges = []
        for i in range(n_dim):
            bounds = np.array([np.percentile(c[:, i], [0.4, 99.6]) for c in chains])
            lo, hi = bounds[:, 0].min(), bounds[:, 1].max()
            pad = 0.08 * (hi - lo)
            ranges.append((float(lo - pad), float(hi + pad)))
    ranges = list(ranges)

    fig = plt.figure(figsize=(width, width), layout="none", **kwargs)
    args = (fig, chains, labels, ranges, colors, truths, smooth)
    if use_corner_pkg and find_spec("corner") is not None:
        axes = _plot_corner_pkg(*args, max_n_ticks)
    else:
        axes = _plot_builtin_corner(*args)

    fig.subplots_adjust(wspace=0.06, hspace=0.06)
    for r in range(n_dim):
        for c in range(n_dim):
            ax = axes[r, c]
            if c > r:
                ax.set_visible(False)
                continue
            ax.set_box_aspect(1.0)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=max_n_ticks, prune="both"))
            ax.tick_params(axis="both", labelrotation=0)
            if r == c:
                ax._is_astro_marginal = True
                ys = [p.get_xy()[:, 1] for p in ax.patches] + [ln.get_ydata() for ln in ax.lines if len(ln.get_ydata()) > 2]
                ymax = max((float(np.max(y)) for y in ys if len(y)), default=0.0)
                ax.set_ylim(0.0, ymax * 1.08 if ymax > 0 else None)
            else:
                ax.yaxis.set_major_locator(MaxNLocator(nbins=max_n_ticks, prune="both"))

    fig.align_ylabels(axes[:, 0])
    fig.align_xlabels(axes[-1, :])

    if names:
        lw = mpl.rcParams["lines.linewidth"] * 1.25
        handles = [Line2D([0], [0], color=colors[i % len(colors)], lw=lw, label=n) for i, n in enumerate(names)]
        fig.legend(
            handles=handles, loc="upper right", bbox_to_anchor=(0.94, 0.94),
            frameon=False, fontsize=mpl.rcParams["legend.fontsize"] * 1.05,
        )
    return fig, axes
