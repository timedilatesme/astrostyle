"""LaTeX detection, axis-label helpers and label linting."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

BASE_TEX_PREAMBLE = r"\usepackage{amsmath,amssymb,bm}"
NEWTX_SNIPPET = r"\usepackage{newtxtext,newtxmath}"

# Axis labels that render the same under usetex and STIX mathtext.
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

_PROBE_DOC = r"""\documentclass{article}
%s
\begin{document}
$\Omega_{\mathrm{m}}, \sigma_8, H_0\,[\mathrm{km\ s^{-1}\ Mpc^{-1}}], \mathrm{\AA}, M_\odot$
\end{document}
"""


def _try_compile_latex(preamble: str) -> bool:
    """Compile a small document to confirm latex, the packages and dvipng all work."""
    if shutil.which("latex") is None or shutil.which("dvipng") is None:
        return False
    run = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "timeout": 8, "check": False}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / "probe.tex"
            tex.write_text(_PROBE_DOC % preamble, encoding="utf-8")
            if subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=tmp, **run).returncode:
                return False
            dvi = tex.with_suffix(".dvi")
            return dvi.exists() and subprocess.run(["dvipng", "-T", "tight", "-o", "probe.png", dvi.name], cwd=tmp, **run).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@lru_cache(maxsize=1)
def detect_tex_support() -> tuple[bool, str]:
    """
    Probe (once per session) whether LaTeX rendering works.

    Returns (True, preamble), preferring newtx Times fonts, or (False, "") so
    callers fall back to STIX mathtext.
    """
    for preamble in (f"{BASE_TEX_PREAMBLE}\n{NEWTX_SNIPPET}", BASE_TEX_PREAMBLE):
        if _try_compile_latex(preamble):
            return True, preamble
    return False, ""


def is_tex_available() -> bool:
    """Return True if a working LaTeX + dvipng toolchain is available."""
    return detect_tex_support()[0]


def unit_label(symbol: str, unit: str | None = None, brackets: str = "[]") -> str:
    r"""
    Build a "symbol [unit]" math label that works with usetex and mathtext.

    >>> unit_label(r"H_0", r"\mathrm{km\ s^{-1}\ Mpc^{-1}}")
    '$H_0\\ [\\mathrm{km\\ s^{-1}\\ Mpc^{-1}}]$'
    """
    sym = symbol.strip().strip("$")
    if not unit:
        return f"${sym}$"
    return rf"${sym}\ {brackets[0]}{unit.strip().strip('$')}{brackets[1]}$"


def _split_math(text: str) -> list[tuple[str, bool]]:
    return [(part, part.startswith("$") and part.endswith("$")) for part in _MATH_SPAN_RE.split(text)]


def escape_tex_outside_math(text: str) -> str:
    """Escape %, & and # that appear outside $...$ math spans."""
    if not text:
        return text
    return "".join(part if is_math else _UNESCAPED_TEX_SPECIAL_RE.sub(r"\\\1", part) for part, is_math in _split_math(text))


def lint_latex_text(text: str, usetex_enabled: bool = False) -> list[str]:
    """Return warnings for unbalanced $, raw sub/superscripts outside math, and unescaped TeX specials."""
    if not text or not text.strip():
        return []
    if len(re.findall(r"(?<!\\)\$", text)) % 2:
        return [f"Unbalanced '$' in label {text!r}."]

    warnings: list[str] = []
    for part, is_math in _split_math(text):
        if is_math:
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
