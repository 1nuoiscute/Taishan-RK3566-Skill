#!/usr/bin/env python3
"""Validate cross-file invariants that quick_validate.py does not cover."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ROOT = DEFAULT_ROOT
REQUIRED_FILES = (
    "VERSION",
    "SKILL.md",
    "claude/SKILL.md",
    "dsh/SKILL.md",
    "dsh/index.mjs",
    "package.json",
    "cordis.patch.yml",
    "skill-src/SKILL.md.tmpl",
    "README.md",
    "agents/openai.yaml",
    ".github/workflows/validate.yml",
    "scripts/generate_skill_entries.py",
    "references/validation-scenarios.md",
    "references/nuedc-topic-coverage.md",
    "references/robust-vision-control.md",
    "references/live-debugging-and-deployment.md",
    "templates/first-use-gate.md",
    "templates/task-intake.md",
    "templates/quick-check-intake.md",
    "templates/solution-options.md",
    "templates/existing-project-change.md",
    "templates/acceptance-checklist.md",
    "templates/perception-control-tuning.md",
    "templates/hardware-evidence-record.md",
    "validation/risk-audit-1.4.0.md",
    "validation/hardware/2026-07-21-historical-baseline.md",
)
STATE_LABELS = ("已确认事实", "用户选择", "合理假设", "待验证")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLATFORM_SKILLS = ("SKILL.md", "claude/SKILL.md", "dsh/SKILL.md")
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
    "references/robust-vision-control.md",
    "references/live-debugging-and-deployment.md",
    "templates/first-use-gate.md",
    "templates/task-intake.md",
    "templates/quick-check-intake.md",
    "templates/solution-options.md",
    "templates/existing-project-change.md",
    "templates/serial-protocol-decision.md",
    "templates/project-architecture.md",
    "templates/acceptance-checklist.md",
    "templates/debug-evidence.md",
    "templates/hardware-evidence-record.md",
    "templates/yolo-data-and-training.md",
    "templates/performance-report.md",
    "templates/perception-control-tuning.md",
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
    "过期",
)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main(root: Path = DEFAULT_ROOT) -> int:
    global ROOT
    ROOT = root.resolve()
    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")

    if errors:
        return finish(errors)

    version = read("VERSION").strip()
    if not re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", version
    ):
        errors.append(f"VERSION is not semantic x.y.z with optional prerelease: {version!r}")

    package = json.loads(read("package.json"))
    if package.get("version") != version:
        errors.append("DSH package version differs from VERSION")
    if package.get("dsh", {}).get("bundle", {}).get("patch") != "./cordis.patch.yml":
        errors.append("DSH bundle patch is missing")
    if "DeepSeek Harness" not in read("dsh/SKILL.md"):
        errors.append("dsh/SKILL.md does not identify DeepSeek Harness")
    readme = read("README.md")
    if f"v{version}" not in readme:
        errors.append("README.md does not contain the VERSION value")

    release_validation_path = f"validation/{version}.md"
    if not (ROOT / release_validation_path).is_file():
        errors.append(f"missing current release validation: {release_validation_path}")
        return finish(errors)

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
    release_validation = read(release_validation_path)
    hardware_record = read("templates/hardware-evidence-record.md")
    hardware_history = read("validation/hardware/2026-07-21-historical-baseline.md")
    workflow = read(".github/workflows/validate.yml")

    template = read("skill-src/SKILL.md.tmpl")
    expected_platform_skills = {
        "SKILL.md": template.replace("{{PLATFORM}}", "Codex"),
        "claude/SKILL.md": template.replace("{{PLATFORM}}", "Claude Code"),
        "dsh/SKILL.md": template.replace("{{PLATFORM}}", "DeepSeek Harness"),
    }
    for relative_path, expected in expected_platform_skills.items():
        if platform_skills[relative_path] != expected:
            errors.append(f"generated Skill entry is stale: {relative_path}")
    if "{{PLATFORM}}" not in template or re.search(r"{{[^}]+}}", template.replace("{{PLATFORM}}", "")):
        errors.append("Skill source template has an invalid platform placeholder")
    for relative_path in PLATFORM_SKILLS:
        if (ROOT / relative_path).stat().st_size > 11234:
            errors.append(f"{relative_path} exceeds the 35% reduction budget of 11234 bytes")

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

    for scenario_id in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        if not re.search(rf"^### {scenario_id}：", scenarios, re.MULTILINE):
            errors.append(f"validation scenarios lack {scenario_id}")
        if not re.search(rf"^\| {scenario_id} .+\|", release_validation, re.MULTILINE):
            errors.append(f"release validation lacks scenario result: {scenario_id}")
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
    robust = read("references/robust-vision-control.md")
    tuning = read("templates/perception-control-tuning.md")
    for phrase in (
        "全帧基线",
        "重捕获",
        "实际采样时间",
        "抗饱和",
        "不得“继续上一帧动作”",
        "固定张数",
    ):
        if phrase not in robust:
            errors.append(f"robust vision/control reference lacks: {phrase}")
    for phrase in ("唯一变量", "回滚", "观测新鲜度", "仍待目标板实测"):
        if phrase not in tuning:
            errors.append(f"perception/control tuning template lacks: {phrase}")
    if "2026 年电赛视觉备赛突击清单" not in read("references/source-index.md"):
        errors.append("source index lacks the 2026 preparation checklist provenance")
    live_debugging = read("references/live-debugging-and-deployment.md")
    for phrase in (
        "节点不存在不等于被占用",
        "最新帧",
        "串口发布频率",
        "宽泛的 `pkill -f`",
        "服务 active",
        "软件零位",
    ):
        if phrase not in live_debugging:
            errors.append(f"live debugging reference lacks: {phrase}")
    if "$taishan-rk3566" not in interface or "首次门禁" not in interface:
        errors.append("agents/openai.yaml default prompt is stale")

    if f"版本：{version}（正式版）" not in release_validation:
        errors.append("release validation does not identify the current VERSION as a formal release")
    if "版本仍标记为 beta" in release_validation:
        errors.append("release validation incorrectly marks the current release as beta")
    for heading in (
        "## 1. 静态检查",
        "## 2. 单元测试",
        "## 3. 合成行为回归",
        "## 4. 探针实板基线",
        "## 5. 项目级端到端验证",
    ):
        if heading not in release_validation:
            errors.append(f"release validation lacks evidence layer: {heading}")
    evidence_statuses = (
        "旧版已实板验证",
        "当前版本仍有效",
        "脚本修改后待复验",
        "从未验证/证据不足",
    )
    for status in evidence_statuses:
        if status not in hardware_record:
            errors.append(f"hardware evidence template lacks status: {status}")
        if status not in hardware_history:
            errors.append(f"historical hardware record lacks status: {status}")
    public_wording = "已有一套历史泰山派探针实测基线，但原始证据归档和当前脚本版本复验仍需完善"
    if public_wording not in readme:
        errors.append("README lacks the approved historical board-evidence wording")
    for command in (
        "python -m unittest discover -s tests -v",
        "scripts/generate_skill_entries.py --check",
        "scripts/validate_skill_content.py",
        "bash -n",
        "git diff --check",
    ):
        if command not in workflow:
            errors.append(f"CI workflow lacks required check: {command}")
    for markdown_file in ROOT.rglob("*.md"):
        if any(part in {".git", "node_modules", "dist", "tmp"} for part in markdown_file.relative_to(ROOT).parts):
            continue
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    sys.exit(main(args.root))
