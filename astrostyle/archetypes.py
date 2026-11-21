"""Aspect-locked publication figure builders covering every astrophysics plot type."""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

from .core import (
    DEFAULT_FRAME_WEIGHT,
    DEFAULT_TEXT_SCALE,
    DOUBLE_COL,
    PALETTES,
    SINGLE_COL,
    ContextName,
    UseTexMode,
    apply_style,
)
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


def fig_xy(
    width: float = SINGLE_COL,
    aspect: float = 0.78,
    *,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "okabe_ito",
    **subplot_kwargs,
):
    """1D curves, SEDs, light curves, scaling relations, and scatter/errorbar plots."""
    apply_style(width, frame_weight, text_scale, context, usetex, palette)
    return plt.subplots(figsize=(width, width * aspect), **subplot_kwargs)


def fig_residuals(
    width: float = SINGLE_COL,
    aspect: float = 1.05,
    height_ratios: tuple[float, float] = (3.0, 1.05),
    *,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "okabe_ito",
    zero_line: bool = True,
):
    """
    Zero-gap stacked data/model + residual figure (spectra, light-curve fits, radial profiles).
    Returns (fig, ax_main, ax_res).
    """
    apply_style(width, frame_weight, text_scale, context, usetex, palette)
    fig, (ax_main, ax_res) = plt.subplots(
        2,
        1,
        figsize=(width, width * aspect),
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios, "hspace": 0.0},
        layout="none",
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
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "okabe_ito",
    **subplot_kwargs,
):
    """
    Aspect-locked 2D image / FITS cutout / surface-brightness map with height-matched external colorbar.
    Returns (fig, ax, cax) when colorbar=True, else (fig, ax).
    """
    apply_style(width, frame_weight, text_scale, context, usetex, palette)
    fig, ax = plt.subplots(
        figsize=(width, width * aspect),
        layout="none",
        **subplot_kwargs,
    )
    ax.set_aspect("equal", adjustable="box")
    ax._auto_tick_contrast = not dark_ticks

    if not colorbar:
        return fig, ax

    return fig, ax, _attach_colorbar_axes(fig, ax, cbar_pad, cbar_width)


def fig_wcs(
    wcs,
    width: float = SINGLE_COL,
    aspect: float = 1.0,
    *,
    colorbar: bool = True,
    cbar_pad: float = 0.03,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
):
    """
    Publication-ready Astropy WCS sky-projection map with inward RA/Dec major & minor ticks.
    Requires `astropy`. Returns (fig, ax, cax) if colorbar=True, else (fig, ax).
    """
    try:
        from astropy.visualization.wcsaxes import WCSAxes  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "fig_wcs() requires astropy. Install with: pip install 'astrostyle[wcs]'"
        ) from exc

    apply_style(width, frame_weight, text_scale, context, usetex)
    fig_w = width * (1.20 if colorbar else 1.0)
    fig = plt.figure(figsize=(fig_w, width * aspect), layout="none")
    ax = fig.add_subplot(111, projection=wcs)
    ax.set_aspect("equal", adjustable="box")
    style_wcs_coords(ax)

    if not colorbar:
        return fig, ax
    return fig, ax, _attach_colorbar_axes(fig, ax, cbar_pad, 0.055)


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
    """Draw a synthesized radio/sub-mm PSF beam ellipse in data units at fractional axis coords."""
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    cx = xlim[0] + loc[0] * (xlim[1] - xlim[0])
    cy = ylim[0] + loc[1] * (ylim[1] - ylim[0])
    ell = Ellipse(
        (cx, cy),
        width=bmin,
        height=bmaj,
        angle=-bpa,
        edgecolor=edgecolor,
        facecolor=facecolor,
        hatch=hatch,
        linewidth=linewidth or (mpl.rcParams["axes.linewidth"] * 0.8),
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
    """Draw a clean physical/angular scale bar in data units on a 2D map."""
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x0 = xlim[0] + loc[0] * (xlim[1] - xlim[0])
    y0 = ylim[0] + loc[1] * (ylim[1] - ylim[0])
    lw = linewidth or (mpl.rcParams["axes.linewidth"] * 1.1)
    ax.plot([x0, x0 + length], [y0, y0], color=color, lw=lw, solid_capstyle="butt", zorder=10)
    ax.text(
        x0 + 0.5 * length,
        y0 + 0.035 * (ylim[1] - ylim[0]),
        label,
        color=color,
        ha="center",
        va="bottom",
        fontsize=mpl.rcParams["xtick.labelsize"],
        fontweight="bold",
        zorder=10,
    )


def fig_grid(
    nrows: int,
    ncols: int,
    width: float | None = None,
    aspect: float | None = None,
    *,
    tight_panels: bool = False,
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "okabe_ito",
    **subplot_kwargs,
):
    """Multi-panel comparison grid with automatic dynamic sizing and optional zero-gap panels."""
    width = width or (SINGLE_COL if ncols == 1 else DOUBLE_COL)
    aspect = aspect or (0.78 * nrows / ncols)
    grid_text_scale = text_scale * (0.90 if ncols >= 3 else 1.0)

    apply_style(width, frame_weight, grid_text_scale, context, usetex, palette)

    if tight_panels:
        subplot_kwargs.setdefault("sharex", True)
        subplot_kwargs.setdefault("sharey", True)
        subplot_kwargs["gridspec_kw"] = {"hspace": 0.0, "wspace": 0.0}
        subplot_kwargs["layout"] = "none"

    fig, axes = plt.subplots(nrows, ncols, figsize=(width, width * aspect), **subplot_kwargs)
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
    """Place bold, consistent panel identifiers ((a), (b), ...) inside panel corners."""
    pos_map = {
        "upper left": (0.04, 0.94, "left", "top"),
        "upper right": (0.96, 0.94, "right", "top"),
        "lower left": (0.04, 0.06, "left", "bottom"),
        "lower right": (0.96, 0.06, "right", "bottom"),
    }
    x, y, ha, va = pos_map[loc]
    flat = list(axes.flat) if hasattr(axes, "flat") else [axes]
    labels = list(labels) if labels is not None else [fmt.format(letter=chr(97 + i)) for i in range(len(flat))]
    fs = fontsize or mpl.rcParams["axes.labelsize"]

    for ax, lab in zip(flat, labels):
        if not ax.get_visible():
            continue
        ax.text(
            x, y, lab,
            transform=ax.transAxes,
            fontsize=fs,
            fontweight="bold",
            color=color,
            ha=ha,
            va=va,
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
    """Add a zoomed-in inset panel with matching bold frame and inward ticks."""
    axins = inset_axes(ax, width=width, height=height, loc=loc, borderpad=0.9)
    axins.set_xlim(*xlim)
    axins.set_ylim(*ylim)
    axins.xaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
    axins.yaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
    axins.tick_params(
        which="both",
        direction="in",
        top=True,
        right=True,
        labelsize=mpl.rcParams["xtick.labelsize"] * 0.85,
    )
    if connect:
        mark_inset(
            ax,
            axins,
            loc1=loc1,
            loc2=loc2,
            fc="none",
            ec="#333333",
            lw=mpl.rcParams["axes.linewidth"] * 0.6,
        )
    return axins


def _credible_levels(hist2d: np.ndarray, probs: tuple[float, ...] = (0.68, 0.95)) -> list[float]:
    """Compute density thresholds enclosing target probability masses (e.g., 68% and 95%)."""
    flat = np.sort(hist2d.ravel())[::-1]
    total = flat.sum()
    if total <= 0:
        return [0.0 for _ in probs]
    cdf = np.cumsum(flat) / total
    levels = []
    for p in sorted(probs, reverse=True):
        idx = np.searchsorted(cdf, p)
        levels.append(float(flat[min(idx, len(flat) - 1)]))
    return levels


def _plot_builtin_corner(
    chains: list[np.ndarray],
    labels: Sequence[str],
    ranges: list[tuple[float, float]],
    colors: list[str],
    truths: Sequence[float] | None,
    fig: mpl.figure.Figure,
    n_bins: int = 38,
    smooth_sigma: float = 1.15,
) -> np.ndarray:
    """Zero-dependency pure NumPy/Matplotlib corner plot with strictly 1:1 square panels."""
    n_dim = len(labels)
    axes = np.atleast_2d(fig.subplots(n_dim, n_dim))

    def _smooth_1d(arr: np.ndarray) -> np.ndarray:
        if smooth_sigma <= 0:
            return arr
        try:
            from scipy.ndimage import gaussian_filter1d
            return gaussian_filter1d(arr, smooth_sigma)
        except ImportError:
            k = np.array([0.2, 0.6, 0.2])
            return np.convolve(arr, k, mode="same")

    def _smooth_2d(arr: np.ndarray) -> np.ndarray:
        if smooth_sigma <= 0:
            return arr
        try:
            from scipy.ndimage import gaussian_filter
            return gaussian_filter(arr, smooth_sigma)
        except ImportError:
            out = np.apply_along_axis(_smooth_1d, 0, arr)
            return np.apply_along_axis(_smooth_1d, 1, out)

    lw_curve = mpl.rcParams["lines.linewidth"]

    for r in range(n_dim):
        for c in range(n_dim):
            ax = axes[r, c]
            if c > r:
                continue

            if r == c:
                lo, hi = ranges[c]
                for i, samples in enumerate(chains):
                    col_color = colors[i % len(colors)]
                    counts, edges = np.histogram(samples[:, c], bins=n_bins, range=(lo, hi), density=True)
                    centers = 0.5 * (edges[:-1] + edges[1:])
                    pdf = _smooth_1d(counts)
                    if pdf.max() > 0:
                        pdf = pdf / pdf.max()
                    ax.plot(centers, pdf, color=col_color, lw=lw_curve)
                    ax.fill_between(centers, 0, pdf, color=col_color, alpha=0.18)
                if truths is not None:
                    ax.axvline(truths[c], color="#444444", ls="--", lw=lw_curve * 0.7)
                ax.set_xlim(lo, hi)
            else:
                xlo, xhi = ranges[c]
                ylo, yhi = ranges[r]
                for i, samples in enumerate(chains):
                    col_color = colors[i % len(colors)]
                    H, xedges, yedges = np.histogram2d(
                        samples[:, c], samples[:, r], bins=n_bins, range=[[xlo, xhi], [ylo, yhi]]
                    )
                    Hs = _smooth_2d(H.T)
                    xc = 0.5 * (xedges[:-1] + xedges[1:])
                    yc = 0.5 * (yedges[:-1] + yedges[1:])
                    lev95, lev68 = _credible_levels(Hs, (0.68, 0.95))
                    hmax = float(Hs.max()) * 1.01
                    if lev95 < lev68 < hmax:
                        ax.contourf(xc, yc, Hs, levels=[lev95, lev68, hmax], colors=[col_color, col_color], alpha=0.22)
                        ax.contourf(xc, yc, Hs, levels=[lev68, hmax], colors=[col_color], alpha=0.25)
                        ax.contour(xc, yc, Hs, levels=[lev95, lev68], colors=[col_color], linewidths=[lw_curve * 0.8, lw_curve])
                if truths is not None:
                    ax.axvline(truths[c], color="#444444", ls="--", lw=lw_curve * 0.65)
                    ax.axhline(truths[r], color="#444444", ls="--", lw=lw_curve * 0.65)
                ax.set_xlim(xlo, xhi)
                ax.set_ylim(ylo, yhi)

            if r == n_dim - 1:
                ax.set_xlabel(labels[c])
            else:
                ax.tick_params(axis="x", labelbottom=False)

            if c == 0 and r > 0:
                ax.set_ylabel(labels[r])
            elif r != c:
                ax.tick_params(axis="y", labelleft=False)

    return axes


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
    frame_weight: float = DEFAULT_FRAME_WEIGHT,
    text_scale: float = DEFAULT_TEXT_SCALE,
    context: ContextName = "paper",
    usetex: UseTexMode = "auto",
    palette: str = "astro_high_contrast",
    use_corner_pkg: bool = True,
):
    """
    Aspect-locked (strictly 1:1 square panels) multi-chain MCMC corner plot.

    Uses `corner` if installed and `use_corner_pkg=True`, and falls back seamlessly
    to a clean zero-dependency NumPy/Matplotlib contour renderer otherwise.
    """
    chain_list = [np.asarray(chains)] if isinstance(chains, np.ndarray) else [np.asarray(c) for c in chains]
    n_dim = chain_list[0].shape[1]
    if len(labels) != n_dim:
        raise ValueError(f"Expected {n_dim} labels matching chain columns, got {len(labels)}.")

    width = width or (DOUBLE_COL if n_dim >= 3 else 4.6)

    corner_text_scale = text_scale * (1.0 if n_dim <= 3 else max(0.78, 1.0 - 0.06 * (n_dim - 3)))
    apply_style(width, frame_weight, corner_text_scale, context, usetex, palette)

    colors = PALETTES.get(palette, PALETTES["astro_high_contrast"])

    if ranges is None:
        computed_ranges = []
        for i in range(n_dim):
            bounds = np.array([np.percentile(c[:, i], [0.4, 99.6]) for c in chain_list])
            lo, hi = bounds[:, 0].min(), bounds[:, 1].max()
            pad = 0.08 * (hi - lo)
            computed_ranges.append((float(lo - pad), float(hi + pad)))
    else:
        computed_ranges = list(ranges)

    fig = plt.figure(figsize=(width, width), layout="none")

    used_external_corner = False
    if use_corner_pkg:
        try:
            import corner  # type: ignore

            for i, samples in enumerate(chain_list):
                c = colors[i % len(colors)]
                rgb = mpl.colors.to_rgb(c)
                corner.corner(
                    samples,
                    fig=fig,
                    labels=list(labels),
                    range=computed_ranges,
                    color=c,
                    truths=truths if i == 0 else None,
                    truth_color="#444444",
                    levels=(0.68, 0.95),
                    smooth=smooth,
                    plot_datapoints=False,
                    plot_density=False,
                    fill_contours=True,
                    contourf_kwargs={"colors": [(*rgb, 0.0), (*rgb, 0.16), (*rgb, 0.32)]},
                    contour_kwargs={"linewidths": mpl.rcParams["lines.linewidth"] * 0.9},
                    hist_kwargs={"density": True, "linewidth": mpl.rcParams["lines.linewidth"]},
                    label_kwargs={
                        "fontsize": mpl.rcParams["axes.labelsize"],
                        "fontweight": "bold",
                    },
                    max_n_ticks=max_n_ticks,
                    use_math_text=True,
                )
            axes = np.array(fig.axes).reshape((n_dim, n_dim))
            used_external_corner = True
        except ImportError:
            used_external_corner = False

    if not used_external_corner:
        axes = _plot_builtin_corner(
            chains=chain_list,
            labels=labels,
            ranges=computed_ranges,
            colors=colors,
            truths=truths,
            fig=fig,
            smooth_sigma=smooth,
        )

    fig.subplots_adjust(wspace=0.06, hspace=0.06)

    for r in range(n_dim):
        for c in range(n_dim):
            ax = axes[r, c]
            if c > r:
                ax.set_visible(False)
                continue
            ax.set_box_aspect(1.0)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=max_n_ticks, prune="both"))
            if r == c:
                ax._is_astro_marginal = True
                ys = [p.get_xy()[:, 1] for p in ax.patches] + [l.get_ydata() for l in ax.lines if len(l.get_ydata()) > 2]
                ymax = max((float(np.max(y)) for y in ys if len(y)), default=0.0)
                ax.set_ylim(0.0, ymax * 1.08 if ymax > 0 else None)
            else:
                ax.yaxis.set_major_locator(MaxNLocator(nbins=max_n_ticks, prune="both"))
            ax.tick_params(axis="both", labelrotation=0)

    fig.align_ylabels(axes[:, 0])
    fig.align_xlabels(axes[-1, :])

    if names:
        handles = [
            Line2D([0], [0], color=colors[i % len(colors)], lw=mpl.rcParams["lines.linewidth"] * 1.25, label=n)
            for i, n in enumerate(names)
        ]
        fig.legend(
            handles=handles,
            loc="upper right",
            bbox_to_anchor=(0.94, 0.94),
            frameon=False,
            fontsize=mpl.rcParams["legend.fontsize"] * 1.05,
        )

    return fig, axes
