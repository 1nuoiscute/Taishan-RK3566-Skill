# 泰山派 RK3566 电赛视觉 Skill

这是一个面向公开用户的 Codex Skill，帮助使用立创·泰山派 RK3566 参加电赛视觉类题目。

它参考 [MaixCAM-skill](https://github.com/LanHua01/MaixCAM-skill) 的工程方法，但不复制 MaixPy、MaixVision 或固定赛题代码。核心流程是：

```text
赛题约束
  -> 视觉任务分类
  -> 传统视觉/测量/跟踪/模型方案比较
  -> 最小板端验证
  -> 坐标、通信和执行闭环
  -> 性能与评分验收
```

## 它能做什么

- 拆解电赛视觉题目的目标、评分、时限、误差和安全约束；
- 在颜色、几何、标定、测量、跟踪、视觉控制、OpenCV 和 RKNN 之间选择路线；
- 规划泰山派 RK3566 与摄像头、UART、GPIO、MSPM0、云台或其他执行机构的职责边界；
- 按 VS Code Remote-SSH 直连板端 Linux 的方式组织开发和调试；
- 生成最小验证、工程结构、调试证据、性能报告和验收清单；
- 接入已有工程，优先局部修改和最小回归。

## 它不会做什么

- 不假设所有用户使用同一个 Linux 镜像、摄像头、设备节点或串口协议；
- 不根据 40 针编号直接猜 Linux GPIO 数字；
- 不在缺少模型、数据集、运行时或板端实测时声称 RKNN 工程已经可交付；
- 不把 MSPM0、云台、电机或安全控制职责擅自迁移到 RK3566；
- 不把桌面电脑上的 FPS、OpenCV 行为或模型结果当作泰山派实测。

## 使用方式

在 Codex 中显式调用：

```text
使用 $taishan-rk3566 分析这道电赛视觉题，并给出可验证的板端实现方案。
```

也可以直接提出具体任务，例如：

```text
使用 $taishan-rk3566，分析这道单目视觉测量题，先给出约束卡和两套可选方案，不要直接写完整工程。
```

## 当前能力状态

| 能力 | 当前状态 | 说明 |
|---|---|---|
| 泰山派原理图和 40 针 IO 约束 | 已有官方资料 | 物理连接和复用功能以原理图、IO 表和设备树共同确认 |
| VS Code Remote-SSH 工作流 | 已确认用户工作流 | VS Code 是界面，代码、编译、运行和日志在板端 Linux |
| 电赛题目拆解 | 已建立方法 | 已收录 2025 C、2025 E、2023 追踪、2024 货架盘点案例 |
| 视觉任务分类 | 已建立初版 | 静态测量、运动跟踪、视觉瞄准、空间盘点、传统识别 |
| OpenCV 运行时 | 已有一套用户板端实测 | 当前样本为 OpenCV 4.13.0；不同镜像仍需重新探测 |
| 摄像头/V4L2 后端 | 已有一套用户板端短基线 | 当前样本为 `/dev/video9`、640×480/YUYV、约 26.66 FPS，不是通用默认值 |
| UART/GPIO 运行时映射 | 部分实测 | 当前样本确认若干 UART 可打开、GPIO chip 可见；映射仍需按设备树和接线确认 |
| RKNN/NPU 部署 | 待版本矩阵和实板验证 | 需要 Toolkit、转换工具、runtime、驱动和模型匹配 |
| 目标板 FPS、延迟、温度和稳定性 | 部分实测 | 已有短时采集/处理 FPS；温度、资源和长时稳定性仍标记为待实测 |

## 目录导航

- `SKILL.md`：触发描述、核心门禁和工作流；
- `references/`：板端运行时、视觉任务、架构、调试、来源和验证方法；
- `templates/`：题目需求、快速验证、方案矩阵、串口决策、工程结构、性能、调试和验收模板；
- `scripts/`：只读板端探针，目前包含系统基线、OpenCV/V4L2 摄像头、安全 UART 监听、GPIO 芯片发现和 RKNN/NPU 运行时发现探针；`run_baseline.sh` 可将五类证据保存到同一目录；
- `examples/vision-uart-baseline/`：摄像头 → LAB/矩形检测 → 可选 UART 的最小端到端参考项目；
- `agents/openai.yaml`：Skill 列表中的界面信息。

## Remote-SSH 与 Codex 边界

VS Code Remote-SSH 能让用户在 VS Code 中操作泰山派，但 Codex 是否能直接执行远程终端命令取决于当前运行环境。若 Codex 只能访问本地工作区，用户需要在 VS Code 的 Remote-SSH 终端运行 `scripts/` 下的探针，再把输出或 JSON 证据交给 Codex；Skill 不会把未执行的命令描述成实板验证。

## 参考资料

- [泰山派 RK3566 官方 Wiki](https://wiki.lckfb.com/zh-hans/tspi-rk3566/)
- [泰山派开源硬件项目](https://oshwhub.com/li-chuang-kai-fa-ban/li-chuang-tai-shan-pai-kai-fa-ban)
- [MaixCAM-skill](https://github.com/LanHua01/MaixCAM-skill)

原始原理图、竞赛题目 PDF、个人工程和未授权模型不直接打包到公开 Skill；来源和适用范围记录在 `references/source-index.md`。
