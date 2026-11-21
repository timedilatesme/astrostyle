"""Automated tests verifying dynamic scaling, inward ticks, LaTeX linting, and exports."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import astrostyle as astro
from astrostyle.latex import escape_tex_outside_math, lint_latex_text


class TestAstroStyle(unittest.TestCase):
    def test_dynamic_width_scaling(self):
        m_single = astro.compute_style_metrics(width=astro.SINGLE_COL)
        m_double = astro.compute_style_metrics(width=astro.DOUBLE_COL)
        self.assertGreater(m_double["label_size"], m_single["label_size"])
        self.assertGreater(m_double["tick_label_size"], m_single["tick_label_size"])
        self.assertAlmostEqual(m_double["axes_linewidth"], astro.DEFAULT_FRAME_WEIGHT, delta=0.05)
        self.assertGreaterEqual(m_single["axes_linewidth"], 1.8)

    def test_inward_major_and_minor_ticks_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fig, ax = astro.fig_xy(usetex=False)
            ax.plot([1, 10, 100], [1, 100, 10000])
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel(r"$x\ [\mathrm{pc}]$")
            ax.set_ylabel(r"$y\ [\mathrm{erg\ s^{-1}}]$")
            issues = astro.polish(fig, verbose=False)
            self.assertEqual(issues, [])
            written = astro.save(fig, tmp_path / "log_test", close=True)
            self.assertEqual(len(written), 2)
            for p in written:
                self.assertTrue(p.exists() and p.stat().st_size > 1000)

    def test_latex_linter_and_escaper(self):
        self.assertEqual(lint_latex_text(r"$\Omega_{\mathrm{m}}$"), [])
        self.assertEqual(lint_latex_text(r"$H_0\ [\mathrm{km\ s^{-1}\ Mpc^{-1}}]$"), [])
        bad = lint_latex_text("Omega_m (km/s)")
        self.assertEqual(len(bad), 1)
        self.assertEqual(
            escape_tex_outside_math(r"68% & 95% contours ($\sigma_8$)"),
            r"68\% \& 95\% contours ($\sigma_8$)",
        )

    def test_corner_plot_square_geometry_and_zero_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rng = np.random.default_rng(0)
            c1 = rng.normal([0.3, 0.8, 67.5], [0.01, 0.01, 0.6], size=(3000, 3))
            c2 = rng.normal([0.29, 0.78, 69.0], [0.015, 0.015, 1.0], size=(3000, 3))
            fig, axes = astro.fig_corner(
                [c1, c2],
                labels=[
                    astro.ASTRO_LABELS["omega_m"],
                    astro.ASTRO_LABELS["sigma_8"],
                    astro.ASTRO_LABELS["h0"],
                ],
                names=["Probe A", "Probe B"],
                usetex=False,
                use_corner_pkg=False,
            )
            self.assertFalse(axes[0, 1].get_visible())
            self.assertFalse(axes[0, 2].get_visible())
            self.assertFalse(axes[1, 2].get_visible())
            self.assertEqual(axes[1, 0].get_box_aspect(), 1.0)
            issues = astro.polish(fig, verbose=False)
            self.assertEqual(issues, [])
            written = astro.save(fig, tmp_path / "corner_test", close=True)
            for p in written:
                self.assertTrue(p.exists())

    def test_auto_rasterize_heavy_scatter(self):
        rng = np.random.default_rng(1)
        fig, ax = astro.fig_xy(usetex=False)
        sc = ax.scatter(rng.normal(size=5000), rng.normal(size=5000), s=2)
        ax.set_xlabel(r"$x$")
        ax.set_ylabel(r"$y$")
        astro.polish(fig, verbose=False)
        self.assertTrue(sc.get_rasterized())
        plt.close(fig)

    def test_builders_inherit_project_style(self):
        with astro.style_context(palette="tol_bright", usetex=False):
            fig, _ = astro.fig_xy()
            self.assertEqual(plt.rcParams["axes.prop_cycle"].by_key()["color"][0], astro.PALETTES["tol_bright"][0])
            plt.close(fig)
            fig, _ = astro.fig_xy(palette="okabe_ito")
            self.assertEqual(plt.rcParams["axes.prop_cycle"].by_key()["color"][0], astro.PALETTES["okabe_ito"][0])
            plt.close(fig)
            fig, _ = astro.fig_xy()
            self.assertEqual(plt.rcParams["axes.prop_cycle"].by_key()["color"][0], astro.PALETTES["tol_bright"][0])
            plt.close(fig)

    def test_guide_text_available(self):
        from astrostyle.guide import get_guide_text
        txt = get_guide_text()
        self.assertIn("astrostyle", txt)
        self.assertIn("fig_corner", txt)


if __name__ == "__main__":
    unittest.main()
