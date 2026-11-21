"""CLI utilities: print the AI agent plotting guide or initialize AGENTS.md in any repo."""

from __future__ import annotations

import argparse
from importlib import resources
from pathlib import Path

AGENTS_STUB = """## Plotting & Figures

All publication figures in this repository MUST use the installed `astrostyle` package.
Before writing or modifying any plotting code:
1. Run `python -m astrostyle.guide` to read the complete API, LaTeX formatting rules, and visual QA contract.
2. Always save figures with `astrostyle.save(fig, "figures/<name>")` and fix any `[astrostyle WARNING]` output before finishing.
"""

CLAUDE_STUB = "@AGENTS.md\n"


def get_guide_text() -> str:
    """Read the bundled AGENT_GUIDE.md from the installed package."""
    return resources.files("astrostyle").joinpath("AGENT_GUIDE.md").read_text(encoding="utf-8")


def main() -> None:
    """Entry point for `python -m astrostyle.guide` and `astrostyle-guide`."""
    print(get_guide_text())


def init_project(argv: list[str] | None = None) -> None:
    """
    Entry point for `astrostyle-init`: appends/creates the short AGENTS.md + CLAUDE.md
    stubs in the current (or target) science project directory.
    """
    parser = argparse.ArgumentParser(
        description="Add a compact AGENTS.md + CLAUDE.md pointer to astrostyle in a project repo."
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory).",
    )
    args = parser.parse_args(argv)
    target = Path(args.target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)

    agents_file = target / "AGENTS.md"
    if agents_file.exists():
        existing = agents_file.read_text(encoding="utf-8")
        if "astrostyle.guide" not in existing:
            agents_file.write_text(existing.rstrip() + "\n\n" + AGENTS_STUB, encoding="utf-8")
            print(f"Appended astrostyle instructions to {agents_file}")
        else:
            print(f"{agents_file} already references astrostyle.")
    else:
        agents_file.write_text(AGENTS_STUB, encoding="utf-8")
        print(f"Created {agents_file}")

    claude_file = target / "CLAUDE.md"
    if not claude_file.exists():
        claude_file.write_text(CLAUDE_STUB, encoding="utf-8")
        print(f"Created {claude_file} -> @AGENTS.md")
    else:
        print(f"{claude_file} already exists (left untouched).")


if __name__ == "__main__":
    main()
