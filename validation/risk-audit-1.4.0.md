# v1.4.0 风险复核报告

日期：2026-08-10

## 裁决摘要

| 批评 | 裁决 | 严重度 | 复核结果 |
|---|---|---|---|
| 实板验证为零、探针从未上板 | 不属实 | 原指控高；实际缺口中 | `cd1bbae` 与当前研究状态记录过 Tspi V10 的 system/camera/UART/GPIO 基线；另有 RKNN 实板案例。缺口是原始证据未归档、camera 0.1.2 待复验。 |
| 无 CI | 属实 | 高 | 整改前所有检查仅记录为本地手工执行，全部 Git 历史中没有 CI 工作流。 |
| 双份 SKILL.md 漂移风险 | 部分属实 | 高 | 旧校验器只检查共享短语和路由，不能保证正文同步；两份文件存在平台适配差异，但无生成机制。 |
| 主文件 17 KB 过重 | 属实 | 中 | 整改前根入口 17,283 字节、132 行；其中大量工作流已可按需路由到 reference。 |

## 1. 历史实板证据链

提交顺序：

1. `171d738`：加入 system 板端探针和 Remote-SSH 证据边界。
2. `af00820`：加入 camera、UART、GPIO、RKNN v0.1.0 探针。
3. `cd1bbae`：修复基线探针、加入统一 runner，并把用户板端结果记录到 README 与 `references/research-status.md`。
4. `a4bb77c`：加入一次脱敏 YOLOv8 RKNN 实板案例。
5. `9cc1f27`：camera 升至 v0.1.2，新增稳定性模式并用两个合成单测修复逻辑；没有记录当前版本摄像头实板复验。

这条链足以否定“从未上板”，但不足以恢复原始命令、退出码和 JSON。历史基线的四类状态见 `validation/hardware/2026-07-21-historical-baseline.md`。

## 2. 回归层级与 R4 遗漏

`references/validation-scenarios.md` 定义 R1–R7 共七个场景。旧版 `validation/1.4.0.md` 只列 R1、R2、R3、R5、R6、R7，遗漏 R4，却仍使用笼统发布判断。整改后的发布记录补齐 R4，并把静态检查、单测、合成回归、探针实板基线和项目级端到端验证分栏。

## 3. CI 与双入口

整改前 `git log --all -- .github` 无结果。现增加 GitHub Actions 执行语法、单测、内容/链接、版本、发布层级、生成一致性和空白检查。

`skill-src/SKILL.md.tmpl` 成为共享正文唯一来源；`scripts/generate_skill_entries.py` 生成根入口和 Claude 入口。CI 的 `--check` 会拦截只修改任意一个生成文件的提交。

## 4. 固定上下文成本

| 入口 | 整改前 | 整改后 | 降幅 |
|---|---:|---:|---:|
| `SKILL.md` | 17,283 字节 / 132 行 | 7,054 字节 / 53 行 | 59.2% |
| `claude/SKILL.md` | 17,051 字节 / 132 行 | 7,060 字节 / 53 行 | 58.6% |

精简后仍常驻：触发描述、四类台账、首次门禁、板端证据边界、接口/闭环安全规则、按需路由和 R1–R7 发布门禁。详细方案、联调和验收内容继续由 references/templates 按需加载。

## 复现命令

```bash
git show --stat cd1bbae
git show cd1bbae -- README.md references/research-status.md scripts
git diff cd1bbae..v1.4.0 -- scripts
git log --all -- .github
python scripts/generate_skill_entries.py --check
python scripts/validate_skill_content.py
python -m unittest discover -s tests -v
bash -n scripts/run_baseline.sh scripts/probe_system.sh
git diff --check
```

对外措辞：**已有一套历史泰山派探针实测基线，但原始证据归档和当前脚本版本复验仍需完善。**
