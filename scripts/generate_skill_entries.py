#!/usr/bin/env python3
"""Generate the Codex, Claude Code, and DeepSeek Harness Skill entry files from one source."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = Path("skill-src/SKILL.md.tmpl")
TARGETS = {
    Path("SKILL.md"): "Codex",
    Path("claude/SKILL.md"): "Claude Code",
    Path("dsh/SKILL.md"): "DeepSeek Harness",
}


def render(template: str, platform: str) -> str:
    rendered = template.replace("{{PLATFORM}}", platform)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("unresolved template placeholder")
    return rendered


def expected_entries(root: Path) -> dict[Path, str]:
    template = (root / TEMPLATE_PATH).read_text(encoding="utf-8")
    return {path: render(template, platform) for path, platform in TARGETS.items()}


def check(root: Path) -> int:
    failed = False
    for relative_path, expected in expected_entries(root).items():
        target = root / relative_path
        actual = target.read_text(encoding="utf-8") if target.is_file() else ""
        if actual == expected:
            continue
        failed = True
        print(f"generated Skill entry is stale: {relative_path}", file=sys.stderr)
        diff = difflib.unified_diff(
            actual.splitlines(), expected.splitlines(),
            fromfile=str(relative_path), tofile=f"generated:{relative_path}", lineterm="",
        )
        for line in list(diff)[:80]:
            print(line, file=sys.stderr)
    return 1 if failed else 0


def write(root: Path) -> int:
    for relative_path, content in expected_entries(root).items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        print(f"generated {relative_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail when generated entries are stale.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    return check(root) if args.check else write(root)


if __name__ == "__main__":
    raise SystemExit(main())
