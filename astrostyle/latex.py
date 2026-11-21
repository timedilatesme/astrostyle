"""LaTeX detection, safe preamble setup, astro symbol helpers, and label linting."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

# Standard astrophysics LaTeX preamble.
# Uses \providecommand so it never conflicts with installed TeX classes/packages.
BASE_TEX_PREAMBLE = r"""
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{bm}
\providecommand{\Msun}{\mathrm{M}_\odot}
\providecommand{\Lsun}{\mathrm{L}_\odot}
\providecommand{\Rsun}{\mathrm{R}_\odot}
\providecommand{\kms}{\mathrm{km\ s^{-1}}}
\providecommand{\angstrom}{\text{\normalfont\AA}}
\providecommand{\arcsec}{^{\prime\prime}}
\providecommand{\arcmin}{^{\prime}}
""".strip()

NEWTX_SNIPPET = r"\usepackage{newtxtext,newtxmath}"

# Ready-to-use astrophysics axis labels compatible with BOTH usetex=True and STIX mathtext.
ASTRO_LABELS = {
    "omega_m": r"$\Omega_{\mathrm{m}}$",
    "omega_lambda": r"$\Omega_{\Lambda}$",
    "sigma_8": r"$\sigma_8$",
    "h0": r"$H_0\ [\mathrm{km\ s^{-1}\ Mpc^{-1}}]$",
    "redshift": r"$z$",
    "wavelength_rest": r"$\lambda_{\mathrm{rest}}\ [\mathrm{\AA}]$",
    "wavelength_obs": r"$\lambda_{\mathrm{obs}}\ [\mathrm{\AA}]$",
    "wavelength_um": r"$\lambda\ [\mu\mathrm{m}]$",
    "log_mstar": r"$\log_{10}(M_\star / M_\odot)$",
    "log_mhalo": r"$\log_{10}(M_{\mathrm{h}} / M_\odot)$",
    "sfr": r"$\mathrm{SFR}\ [M_\odot\ \mathrm{yr}^{-1}]$",
    "luminosity_distance": r"$d_L(z)\ [\mathrm{Gpc}]$",
    "flux_lambda": r"$F_\lambda\ [10^{-17}\ \mathrm{erg\ s^{-1}\ cm^{-2}\ \AA^{-1}}]$",
    "residual": r"$\Delta F / \sigma$",
    "surface_brightness": r"$\log_{10}\,\Sigma\ [L_\odot\ \mathrm{kpc}^{-2}]$",
}

_MATH_SPAN_RE = re.compile(r"(\$[^$]*\$)")
_RAW_SUB_SUP_RE = re.compile(r"[A-Za-z0-9]+[_^][A-Za-z0-9]+")
_UNESCAPED_TEX_SPECIAL_RE = re.compile(r"(?<!\\)([%&#])")


def _try_compile_latex(preamble: str) -> bool:
    """Actually compile a minimal LaTeX snippet to confirm TeX + packages + dvipng work."""
    if shutil.which("latex") is None or shutil.which("dvipng") is None:
        return False

    doc = (
        "\\documentclass{article}\n"
        f"{preamble}\n"
        "\\begin{document}\n"
        "$\\Omega_{\\mathrm{m}}, \\sigma_8, H_0\\,[\\mathrm{km\\ s^{-1}\\ Mpc^{-1}}], \\mathrm{\\AA}, M_\\odot$\n"
        "\\end{document}\n"
    )
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "probe.tex"
            tex_file.write_text(doc, encoding="utf-8")
            res = subprocess.run(
                ["latex", "-interaction=nonstopmode", "-halt-on-error", str(tex_file)],
                cwd=tmpdir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
            )
            if res.returncode != 0:
                return False
            dvi_file = Path(tmpdir) / "probe.dvi"
            if not dvi_file.exists():
                return False
            res2 = subprocess.run(
                ["dvipng", "-T", "tight", "-o", str(Path(tmpdir) / "probe.png"), str(dvi_file)],
                cwd=tmpdir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
            )
            return res2.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@lru_cache(maxsize=1)
def detect_tex_support() -> tuple[bool, str]:
    """
    Detect once per Python session whether full LaTeX rendering works.

    Returns (True, preamble) when latex + dvipng compile cleanly (preferring
    newtxtext/newtxmath to match ApJ/MNRAS/A&A Times/STIX), or (False, "")
    to fall back seamlessly to built-in STIX mathtext.
    """
    full_preamble = f"{BASE_TEX_PREAMBLE}\n{NEWTX_SNIPPET}"
    if _try_compile_latex(full_preamble):
        return True, full_preamble
    if _try_compile_latex(BASE_TEX_PREAMBLE):
        return True, BASE_TEX_PREAMBLE
    return False, ""


def is_tex_available() -> bool:
    """Return True if a working LaTeX + dvipng toolchain is available."""
    return detect_tex_support()[0]


def unit_label(symbol: str, unit: str | None = None, brackets: str = "[]") -> str:
    r"""
    Build a cleanly formatted LaTeX axis label compatible with both usetex and STIX mathtext.

    Examples
    --------
    >>> unit_label(r"H_0", r"\mathrm{km\ s^{-1}\ Mpc^{-1}}")
    '$H_0\\ [\\mathrm{km\\ s^{-1}\\ Mpc^{-1}}]$'
    """
    sym = symbol.strip().strip("$")
    if not unit:
        return f"${sym}$"
    u = unit.strip().strip("$")
    left, right = brackets[0], brackets[1]
    return rf"${sym}\ {left}{u}{right}$"


def escape_tex_outside_math(text: str) -> str:
    """
    Escape TeX-special characters (%, &, #) that appear outside $...$ math spans.
    Safe to call on legends/annotations when text.usetex=True.
    """
    if not text:
        return text
    parts = _MATH_SPAN_RE.split(text)
    out = []
    for part in parts:
        if part.startswith("$") and part.endswith("$"):
            out.append(part)
        else:
            out.append(_UNESCAPED_TEX_SPECIAL_RE.sub(r"\\\1", part))
    return "".join(out)


def lint_latex_text(text: str, usetex_enabled: bool = False) -> list[str]:
    """
    Check a plot label or legend string for common LaTeX / mathtext mistakes.
    Returns a list of human-readable warning strings.
    """
    if not text or not text.strip():
        return []

    warnings: list[str] = []

    unescaped_dollars = len(re.findall(r"(?<!\\)\$", text))
    if unescaped_dollars % 2 != 0:
        warnings.append(f"Unbalanced '$' in label {text!r}.")
        return warnings

    parts = _MATH_SPAN_RE.split(text)
    for part in parts:
        if part.startswith("$") and part.endswith("$"):
            continue
        if _RAW_SUB_SUP_RE.search(part):
            warnings.append(
                f"Raw subscript/superscript in {text!r} outside math mode; "
                "wrap symbols in LaTeX math (e.g. r'$\\Omega_{{\\mathrm{{m}}}}$')."
            )
        if usetex_enabled and _UNESCAPED_TEX_SPECIAL_RE.search(part):
            warnings.append(
                f"Unescaped TeX character (%, &, or #) in {text!r} while usetex=True; "
                "escape with backslash or use escape_tex_outside_math()."
            )

    return warnings
