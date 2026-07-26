#!/usr/bin/env python3
"""Validate cross-file invariants that quick_validate.py does not cover."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "VERSION",
    "SKILL.md",
    "claude/SKILL.md",
    "README.md",
    "agents/openai.yaml",
    "references/validation-scenarios.md",
    "references/nuedc-topic-coverage.md",
    "templates/first-use-gate.md",
    "templates/task-intake.md",
    "templates/quick-check-intake.md",
    "templates/solution-options.md",
    "templates/existing-project-change.md",
    "templates/acceptance-checklist.md",
)
STATE_LABELS = ("已确认事实", "用户选择", "合理假设", "待验证")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLATFORM_SKILLS = ("SKILL.md", "claude/SKILL.md")
SHARED_ROUTES = (
    "references/source-index.md",
    "references/nuedc-topic-coverage.md",
    "references/research-guidance.md",
    "references/board-and-runtime.md",
    "references/vision-task-archetypes.md",
    "references/architecture-patterns.md",
    "references/debugging-playbook.md",
    "references/existing-project-integration.md",
    "references/validation-and-evidence.md",
    "references/validation-scenarios.md",
    "references/yolo-rknn-validated-case.md",
    "templates/first-use-gate.md",
    "templates/task-intake.md",
    "templates/quick-check-intake.md",
    "templates/solution-options.md",
    "templates/existing-project-change.md",
    "templates/serial-protocol-decision.md",
    "templates/project-architecture.md",
    "templates/acceptance-checklist.md",
    "templates/debug-evidence.md",
    "templates/yolo-data-and-training.md",
    "templates/performance-report.md",
)
BEHAVIOR_INVARIANTS = (
    "首次使用门禁",
    "部分通过",
    "合理假设",
    "最小验证",
    "降级路线",
    "不直接生成完整闭环代码",
    "R1、R2、R3",
    "不能发布该版本",
    "证据保存",
    "回滚办法",
)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")

    if errors:
        return finish(errors)

    version = read("VERSION").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"VERSION is not semantic x.y.z: {version!r}")

    readme = read("README.md")
    if f"v{version}" not in readme:
        errors.append("README.md does not contain the VERSION value")

    platform_skills = {
        relative_path: read(relative_path) for relative_path in PLATFORM_SKILLS
    }
    skill = platform_skills["SKILL.md"]
    claude_skill = platform_skills["claude/SKILL.md"]
    gate = read("templates/first-use-gate.md")
    task_intake = read("templates/task-intake.md")
    quick_intake = read("templates/quick-check-intake.md")
    solution_options = read("templates/solution-options.md")
    existing_change = read("templates/existing-project-change.md")
    topic_coverage = read("references/nuedc-topic-coverage.md")
    scenarios = read("references/validation-scenarios.md")
    interface = read("agents/openai.yaml")

    for label in STATE_LABELS:
        for relative_path, content in (
            *platform_skills.items(),
            ("templates/first-use-gate.md", gate),
            ("templates/task-intake.md", task_intake),
            ("templates/quick-check-intake.md", quick_intake),
            ("templates/solution-options.md", solution_options),
        ):
            if label not in content:
                errors.append(f"{relative_path} lacks state label: {label}")

    for field in ("板卡", "系统", "摄像头", "接口", "题目"):
        if field not in gate:
            errors.append(f"first-use gate lacks required field: {field}")

    for outcome in ("通过", "部分通过", "阻塞"):
        if outcome not in gate:
            errors.append(f"first-use gate lacks outcome: {outcome}")

    for scenario_id in ("R1", "R2", "R3", "R4"):
        if scenario_id not in scenarios:
            errors.append(f"validation scenarios lack {scenario_id}")
    if "scripts/probe_camera.py" not in scenarios:
        errors.append("R3 does not point to the existing camera project artifact")

    for phrase in ("最小修改面", "回滚办法", "原有行为回归", "新功能最小验证"):
        if phrase not in existing_change:
            errors.append(f"existing-project template lacks: {phrase}")

    for phrase in ("最小验证", "失败信号", "降级路线", "主类型"):
        if phrase not in topic_coverage:
            errors.append(f"topic coverage lacks decision element: {phrase}")

    for relative_path, content in platform_skills.items():
        for required_reference in SHARED_ROUTES:
            if required_reference not in content:
                errors.append(f"{relative_path} does not route to: {required_reference}")
            if not (ROOT / required_reference).is_file():
                errors.append(f"{relative_path} routes to missing file: {required_reference}")
        for invariant in BEHAVIOR_INVARIANTS:
            if invariant not in content:
                errors.append(f"{relative_path} lacks behavior invariant: {invariant}")

    if "examples/vision-uart-baseline" in skill:
        errors.append("SKILL.md references the nonexistent UART end-to-end example")
    if "Codex" not in skill:
        errors.append("SKILL.md does not identify the Codex platform")
    if "Claude Code" not in claude_skill:
        errors.append("claude/SKILL.md does not identify the Claude Code platform")
    if "../references/" in claude_skill or "../templates/" in claude_skill:
        errors.append("claude/SKILL.md assumes repository layout instead of installed layout")
    if "yolo-rknn-validated-case.md" not in read("templates/yolo-data-and-training.md"):
        errors.append("YOLO template does not link the validated RKNN case")
    if "$taishan-rk3566" not in interface or "首次门禁" not in interface:
        errors.append("agents/openai.yaml default prompt is stale")
    for markdown_file in ROOT.rglob("*.md"):
        content = markdown_file.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(content):
            target = raw_target.strip().split("#", 1)[0]
            if not target or re.match(r"^[a-z]+://", target, re.IGNORECASE):
                continue
            resolved = (markdown_file.parent / target).resolve()
            if not resolved.exists():
                relative_file = markdown_file.relative_to(ROOT)
                errors.append(f"broken local link in {relative_file}: {raw_target}")

    return finish(errors)


def finish(errors: list[str]) -> int:
    if errors:
        print("content validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("content validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
