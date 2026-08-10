# 2026-07-21 历史泰山派实板基线

## 记录性质

这是根据 Git 提交 `cd1bbae306ee7d4232ed15a2d32ecec99859fc3e` 和当前 `references/research-status.md` 恢复的历史记录。提交标题为 `fix baseline probes and document board evidence`，其父提交为首次加入 camera/UART/GPIO/RKNN 探针的 `af00820`。

仓库没有保留本次运行的原始 JSON、stderr、完整命令、精确执行时间或退出码，因此这些字段保持未知。本记录证明仓库曾记录过实板探针结果，但不是可重新计算的原始证据包。

整体历史状态为“旧版已实板验证”；下表再按当前代码是否变化细分为“当前版本仍有效”“脚本修改后待复验”和“从未验证/证据不足”。

## 身份与结果摘要

- 板卡：Tspi V10
- 系统：Ubuntu 20.04.6，Linux 4.19.232，aarch64
- OpenCV：4.13.0
- 对应探针版本：camera/UART/GPIO/RKNN `0.1.0`；system 探针由 `cd1bbae` 同次修复
- 脚本 Git SHA：`cd1bbae306ee7d4232ed15a2d32ecec99859fc3e`（文字记录所关联的仓库状态）
- 原始证据 SHA-256：未知，原始文件未进入仓库

| 能力 | 当前证据状态 | 历史摘要 | 当前边界 |
|---|---|---|---|
| system | 当前版本仍有效 | 记录了板卡、系统、内核和架构 | 当前脚本自该提交后未变，但不同镜像仍需重跑 |
| camera | 脚本修改后待复验 | `640x480/YUYV` 短时约 26.66 FPS | v1.4.0 升至 0.1.2 并新增稳定性模式；该模式只有合成单测，没有当前版实板证据 |
| UART | 当前版本仍有效 | 历史发布说明记录若干 UART 可打开 | 只证明当时环境可见/可打开，不证明接线、对端或协议正确 |
| GPIO | 当前版本仍有效 | 历史发布说明记录 GPIO chip 可见 | 不证明 pinmux、物理针脚映射或 line 读写 |
| RKNN | 从未验证/证据不足 | 同期探针存在，但历史说明仍将 RKNN 部署列为待验证 | 另有特定 YOLOv8 RKNN 实板案例，不等于这次基线保留了 RKNN 探针原始结果 |

## 可复现历史查询

```bash
git show --stat cd1bbae
git show cd1bbae -- README.md references/research-status.md scripts
git log --follow -- scripts/probe_camera.py scripts/probe_uart.py scripts/probe_gpio.py scripts/probe_rknn.py
git diff cd1bbae..v1.4.0 -- scripts
```

对外统一措辞：**已有一套历史泰山派探针实测基线，但原始证据归档和当前脚本版本复验仍需完善。**
