"""Smoke-test gallery generating all 4 publication astrophysics archetypes (PDF + PNG)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import astrostyle as astro


def make_spectrum_residuals(out_dir: Path) -> None:
    rng = np.random.default_rng(42)
    lam = np.linspace(4800.0, 5060.0, 260)

    def model(x):
        cont = 1.2 - 0.0005 * (x - 4930.0)
        hb = 3.2 * np.exp(-0.5 * ((x - 4861.3) / 6.5) ** 2)
        o3a = 2.6 * np.exp(-0.5 * ((x - 4958.9) / 6.5) ** 2)
        o3b = 7.8 * np.exp(-0.5 * ((x - 5006.8) / 6.5) ** 2)
        return cont + hb + o3a + o3b

    flux_mod = model(lam)
    sigma = np.full_like(lam, 0.28)
    flux_obs = flux_mod + rng.normal(0.0, sigma)
    resid = (flux_obs - flux_mod) / sigma

    fig, ax_main, ax_res = astro.fig_residuals(width=astro.SINGLE_COL)
    ax_main.errorbar(lam[::2], flux_obs[::2], yerr=sigma[::2], fmt="o", ms=2.6, color="#222222", alpha=0.65, label=r"Observed")
    ax_main.plot(lam, flux_mod, color="#0072B2", label=r"Best-fit model")
    ax_main.set_ylabel(r"$F_\lambda\ [10^{-17}\ \mathrm{cgs}]$")
    ax_main.legend(loc="upper left")

    ax_res.errorbar(lam[::2], resid[::2], yerr=1.0, fmt="o", ms=2.2, color="#222222", alpha=0.65)
    ax_res.set_ylim(-3.5, 3.5)
    ax_res.set_xlabel(astro.ASTRO_LABELS["wavelength_rest"])
    ax_res.set_ylabel(astro.ASTRO_LABELS["residual"])

    astro.save(fig, out_dir / "01_spectrum_residuals", close=True)


def make_cosmology_curves(out_dir: Path) -> None:
    z = np.linspace(0.05, 3.0, 240)
    c_over_h0 = 299792.458 / 70.0 / 1000.0  # Gpc

    def dl_flat_lcdm(z_arr, om=0.3, ol=0.7):
        out = np.empty_like(z_arr)
        for i, zi in enumerate(z_arr):
            zs = np.linspace(0.0, zi, 300)
            ez = np.sqrt(om * (1.0 + zs) ** 3 + ol)
            integral = np.trapezoid(1.0 / ez, zs) if hasattr(np, "trapezoid") else np.trapz(1.0 / ez, zs)
            out[i] = (1.0 + zi) * c_over_h0 * integral
        return out

    dl_lcdm = dl_flat_lcdm(z, 0.3, 0.7)
    dl_eds = 2.0 * c_over_h0 * (1.0 + z) * (1.0 - 1.0 / np.sqrt(1.0 + z))
    dl_milne = c_over_h0 * z * (1.0 + 0.5 * z)

    fig, ax = astro.fig_xy(width=astro.SINGLE_COL)
    ax.fill_between(z, 0.94 * dl_lcdm, 1.06 * dl_lcdm, color="#0072B2", alpha=0.22)
    ax.plot(z, dl_lcdm, label=r"$\Lambda\mathrm{CDM}\ (\Omega_{\mathrm{m}}=0.3)$")
    ax.plot(z, dl_milne, ls="--", label=r"$\mathrm{Milne}\ (\Omega_{\mathrm{m}}=0)$")
    ax.plot(z, dl_eds, ls=":", label=r"$\mathrm{EdS}\ (\Omega_{\mathrm{m}}=1)$")
    ax.set_xlabel(astro.ASTRO_LABELS["redshift"])
    ax.set_ylabel(astro.ASTRO_LABELS["luminosity_distance"])
    ax.set_xlim(0.0, 3.0)
    ax.set_ylim(0.0, 28.0)
    ax.legend(loc="upper left")

    astro.save(fig, out_dir / "02_cosmology_curves", close=True)


def make_sersic_map(out_dir: Path) -> None:
    x = np.linspace(-8.0, 8.0, 220)
    X, Y = np.meshgrid(x, x)
    pa = np.deg2rad(35.0)
    xr = X * np.cos(pa) + Y * np.sin(pa)
    yr = -X * np.sin(pa) + Y * np.cos(pa)
    r_ell = np.sqrt(xr ** 2 + (yr / 0.65) ** 2)
    n, re = 2.0, 2.5
    bn = 2.0 * n - 1.0 / 3.0
    log_sb = 9.2 - (bn / np.log(10.0)) * ((r_ell / re) ** (1.0 / n) - 1.0)

    fig, ax, cax = astro.fig_image(width=astro.SINGLE_COL)
    im = ax.imshow(log_sb, extent=[-8, 8, -8, 8], vmin=6.2, vmax=9.8, cmap="inferno")
    ax.contour(X, Y, log_sb, levels=[7.2, 8.0, 8.8], colors="white", linewidths=1.0, alpha=0.75)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label(astro.ASTRO_LABELS["surface_brightness"])
    ax.set_xlabel(r"$\Delta x\ [\mathrm{kpc}]$")
    ax.set_ylabel(r"$\Delta y\ [\mathrm{kpc}]$")
    astro.add_scalebar(ax, length=4.0, label=r"$4\,\mathrm{kpc}$", loc=(0.64, 0.10))

    astro.save(fig, out_dir / "03_sersic_map", close=True)


def make_corner_plot(out_dir: Path) -> None:
    rng = np.random.default_rng(7)
    mean_a = np.array([0.315, 0.811, 67.4])
    std_a = np.array([0.008, 0.007, 0.55])
    corr_a = np.array([
        [1.00, 0.55, -0.82],
        [0.55, 1.00, -0.42],
        [-0.82, -0.42, 1.00],
    ])
    cov_a = np.outer(std_a, std_a) * corr_a

    mean_b = np.array([0.296, 0.784, 69.3])
    std_b = np.array([0.014, 0.015, 1.05])
    corr_b = np.array([
        [1.00, -0.62, -0.35],
        [-0.62, 1.00, 0.22],
        [-0.35, 0.22, 1.00],
    ])
    cov_b = np.outer(std_b, std_b) * corr_b

    chain_a = rng.multivariate_normal(mean_a, cov_a, size=12000)
    chain_b = rng.multivariate_normal(mean_b, cov_b, size=12000)

    fig, _ = astro.fig_corner(
        [chain_a, chain_b],
        labels=[
            astro.ASTRO_LABELS["omega_m"],
            astro.ASTRO_LABELS["sigma_8"],
            astro.ASTRO_LABELS["h0"],
        ],
        names=[r"Planck CMB", r"DES Lensing + BAO"],
        width=astro.DOUBLE_COL,
    )
    astro.save(fig, out_dir / "04_corner_mcmc", close=True)


def main() -> None:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "gallery_output")
    print(f"LaTeX toolchain detected: {astro.is_tex_available()}")
    make_spectrum_residuals(out_dir)
    make_cosmology_curves(out_dir)
    make_sersic_map(out_dir)
    make_corner_plot(out_dir)
    print(f"Saved gallery PDFs and PNGs to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
