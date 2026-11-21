"""astrostyle: Dynamic, journal-agnostic astrophysics publication plotting."""

from .archetypes import (
    add_beam,
    add_inset,
    add_scalebar,
    fig_corner,
    fig_grid,
    fig_image,
    fig_residuals,
    fig_wcs,
    fig_xy,
    label_panels,
)
from .core import (
    COLORMAPS,
    DEFAULT_FRAME_WEIGHT,
    DEFAULT_TEXT_SCALE,
    DOUBLE_COL,
    PALETTES,
    SINGLE_COL,
    apply_style,
    compute_style_metrics,
    get_active_config,
    style_context,
)
from .latex import (
    ASTRO_LABELS,
    escape_tex_outside_math,
    is_tex_available,
    unit_label,
)
from .polish import lint_fig, polish, save

__all__ = [
    "SINGLE_COL",
    "DOUBLE_COL",
    "DEFAULT_FRAME_WEIGHT",
    "DEFAULT_TEXT_SCALE",
    "PALETTES",
    "COLORMAPS",
    "ASTRO_LABELS",
    "apply_style",
    "compute_style_metrics",
    "get_active_config",
    "style_context",
    "is_tex_available",
    "unit_label",
    "escape_tex_outside_math",
    "fig_xy",
    "fig_residuals",
    "fig_image",
    "fig_wcs",
    "fig_grid",
    "fig_corner",
    "label_panels",
    "add_inset",
    "add_beam",
    "add_scalebar",
    "polish",
    "lint_fig",
    "save",
]

__version__ = "0.1.0"
