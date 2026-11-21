# astrostyle — AI Agent Plotting Contract

All figures in this repository MUST be generated using the installed `astrostyle` package so they are publication-ready and journal-agnostic across ApJ/AJ/ApJS, MNRAS, A&A, and Nature Astronomy.

## 1. Mandatory Archetype Builders (Never use raw `plt.figure()` with default styling)

Import directly from `astrostyle`:

```python
import astrostyle as astro
```

Choose the matching builder for the figure type:

- **1D curves, SEDs, light curves, scaling relations, scatter/errorbars**
  `fig, ax = astro.fig_xy(width=astro.SINGLE_COL)`
- **Data + model + stacked residuals (spectra, transit/radial fits)**
  `fig, ax_main, ax_res = astro.fig_residuals(width=astro.SINGLE_COL)`
- **2D maps, FITS cutouts, surface brightness, density maps (square 1:1 + matched colorbar)**
  `fig, ax, cax = astro.fig_image(width=astro.SINGLE_COL)` -> always pass `cax=cax` to `fig.colorbar(im, cax=cax)`
- **Astropy WCS sky projections (RA/Dec inward ticks)**
  `fig, ax, cax = astro.fig_wcs(wcs, width=astro.SINGLE_COL)` -> optional `astro.add_beam(...)`, `astro.add_scalebar(...)`
- **Multi-panel grids**
  `fig, axes = astro.fig_grid(nrows, ncols, width=astro.DOUBLE_COL, tight_panels=...)` + `astro.label_panels(axes)`
- **MCMC posterior corner plots (strictly square 1:1 cells)**
  `fig, axes = astro.fig_corner([chain1, chain2], labels=[...], names=[...])`
- **Zoomed-in inset panel**
  `axins = astro.add_inset(ax, xlim=(...), ylim=(...))`
- **Custom layouts / GridSpec / Seaborn**
  Call `astro.apply_style(width=astro.DOUBLE_COL)` BEFORE creating axes, and ALWAYS finalize with `astro.save(fig, "figures/<name>")` so `astro.polish(fig)` enforces thick frames, inward major+minor ticks, and linting.

## 2. Print Dimensions & Aspect Ratios

- Use `astro.SINGLE_COL` (`3.50 in`) for single panels or 2 vertically stacked panels.
- Use `astro.DOUBLE_COL` (`7.10 in`) for side-by-side grids, wide figures, or 3+ parameter corner plots.
- **Never stretch square plots**: corner plots and 2D maps are aspect-locked (`1:1`). Do not override `set_box_aspect(1.0)` or `set_aspect("equal")`.
- Do NOT override font sizes, tick lengths, or spine widths manually unless fixing a verified layout collision. The style scales borders (`2.4 pt` base), inward major+minor ticks, and bold typography dynamically with `width`.

## 3. Strict LaTeX & Physical Unit Formatting

- **Always format mathematical symbols and units with raw LaTeX strings (`r"..."`)**:
  - GOOD: `r"$\Omega_{\mathrm{m}}$"`, `r"$\sigma_8$"`, `r"$H_0\ [\mathrm{km\ s^{-1}\ Mpc^{-1}}]$"`, `r"$\lambda_{\mathrm{rest}}\ [\mathrm{\AA}]$"`, `r"$\log_{10}(M_\star / M_\odot)$"`
  - BAD: `"Omega_m"`, `"sigma_8"`, `"H_0 (km/s/Mpc)"`, `"log(M_star)"`, `"flux (1e-17)"`
- Helper shortcuts are available in `astro.ASTRO_LABELS` and `astro.unit_label(symbol, unit)`.
- `astrostyle` runs with `usetex="auto"` (uses real LaTeX with `amsmath, amssymb, bm, newtx` when available, and seamlessly falls back to STIX mathtext when TeX is absent). Keep math notation compatible with both: use standard LaTeX (`\mathrm{}`, `\log_{10}`, `\AA`, `\odot`, `\mu`, `\sigma`, `\Omega`, `\lambda`).
- Escape `%` as `\%` inside text strings if passing `usetex=True`, or let `astro.polish(fig)` sanitize it.
- **Never add top figure titles on single-panel paper figures** — titles belong in the LaTeX caption.

## 4. Color, Grids, Ticks & Heavy Data Discipline

- **No background grids** (`axes.grid` is `False`).
- **Both major and minor ticks MUST point inward on all four sides** (automatically enforced by `astro.polish()`).
- Use the default colorblind-safe discrete palette (do not invent arbitrary hex colors or `red`/`green` pairs).
- Colormaps: `inferno`, `magma`, `viridis`, or `cividis` for intensity/density; `RdBu_r` centered at zero (`TwoSlopeNorm`) for velocity or residuals. **Never use `jet` or `rainbow`.**
- Dense scatter/mesh plots (`> 3,000` points) are automatically rasterized by `astro.polish(fig)` so PDFs stay small while text and axes remain vector.

## 5. Mandatory Export & Visual QA Loop

1. Always save via `astro.save(fig, "figures/<descriptive_name>")` (outputs both editable vector `.pdf` and `300 dpi` `.png`).
2. Read stdout carefully: if `[astrostyle WARNING]` reports overlapping tick labels or raw non-LaTeX subscripts, **fix the root cause** (e.g., `MaxNLocator(nbins=3, prune="both")` or raw LaTeX strings) and re-run until there are zero warnings.
3. If you can view images, open the saved `.png` and confirm:
   - Thick frames and inward major + minor ticks are clearly visible on all 4 sides (and white over dark 2D maps).
   - Every LaTeX symbol, subscript, superscript, and unit rendered properly (no raw `_`, `^`, or literal `\`).
   - Axis labels, tick numbers, and legends are large, bold, unclipped, and non-overlapping.
   - Corner plots and 2D maps have square `1:1` panels.
