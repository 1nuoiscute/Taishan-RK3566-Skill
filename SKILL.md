---
name: taishan-rk3566
description: Plan, implement, debug, and validate NUEDC-style computer-vision projects for the Lichuang Taishan RK3566 board. Use when a user needs to decompose a vision competition problem, choose between classical vision, geometry, tracking, or model inference, connect vision to GPIO/UART/gimbals or lower controllers, develop through VS Code Remote-SSH or another board-side Linux workflow, or produce a testable project and acceptance evidence. Do not use as a generic RK3566 Linux reference when the task has no competition-vision or board-integration context.
---

# 泰山派 RK3566 电赛视觉 Skill

面向公开用户，按 MaixCAM-skill 的工程方法帮助完成电赛视觉题：先读题和约束，再选择可验证的视觉路线，最后完成板端实现、闭环联调和按评分指标验收。保持摄像头、系统镜像、通信协议、模型和下位机可替换，不把某一届题目或个人工程写成固定答案。

## 资料导航

只在需要时读取相关资料，避免一次加载全部参考文档。

- **资料和来源边界**：读取 [source-index.md](references/source-index.md)。区分官方硬件资料、官方 Wiki 的“共建”案例、竞赛题目和待验证经验。
- **题目索引和陌生题**：读取 [nuedc-topic-coverage.md](references/nuedc-topic-coverage.md)。先匹配视觉模式，再处理陌生题；不要强套历史题。
- **研究和来源分级**：读取 [research-guidance.md](references/research-guidance.md)。题目规则、硬件、版本、API 或路线存在不确定性时使用。
- **板端环境发现**：读取 [board-and-runtime.md](references/board-and-runtime.md)。适用于 VS Code Remote-SSH 直连、摄像头、GPIO、UART、OpenCV 和模型运行时检查。
- **真实基线探测**：运行 `scripts/run_baseline.sh`，或按需运行 `scripts/probe_*.py` 与 `scripts/probe_system.sh`；保存 JSON、stderr 和命令版本后再称为“实板基线”。
- **首次使用门禁**：读取 `templates/first-use-gate.md`。首次用户、新题目、环境变化或来源不明的已有工程都先使用。
- **视觉任务分类**：读取 [vision-task-archetypes.md](references/vision-task-archetypes.md)。题目涉及测量、跟踪、瞄准、空间盘点或其他视觉任务时，只加载匹配章节。
- **工程架构**：读取 [architecture-patterns.md](references/architecture-patterns.md)。方案确认后确定模块、状态和可替换点。
- **调试顺序**：读取 [debugging-playbook.md](references/debugging-playbook.md)。出现采集、算法、模型、通信、闭环或性能问题时使用。
- **已有工程接入**：读取 [existing-project-integration.md](references/existing-project-integration.md)。用户提供代码、协议、接线或运行工程时先使用。
- **验证和证据**：读取 [validation-and-evidence.md](references/validation-and-evidence.md)。需要性能、误差、闭环或验收结论时使用。
- **发布前回归**：读取 [validation-scenarios.md](references/validation-scenarios.md)。修改 Skill、模板或参考资料后执行匹配场景。
- **需求模板**：按需使用 `templates/` 下的需求、方案、架构和验收模板；已有工程增量改造使用 `templates/existing-project-change.md`。

## 硬规则

1. 首次使用、新题目、环境变化或已有工程信息不足时，先执行首次使用门禁；主动收集板卡、系统、摄像头、相关接口和题目约束，再决定只做探测、进入方案验证或开始工程。
2. 将信息标为“已确认事实”“用户选择”“合理假设”或“待验证”。不能把搜索结果、社区案例或猜测写成板卡事实。
3. 以官方原理图和 IO 表确认物理连接；以当前 Linux 镜像、内核和设备树确认运行时接口。不要凭 `GPIOx_y` 臆测 Linux GPIO 数字，不要假设固定 `/dev/video*`、串口名或摄像头后端。
4. 复用功能必须通过 Pinmux/设备树确认，不能声称同一个引脚同时承担多个功能。3.3 V、5 V 和 GND 引脚不是 GPIO。
5. 优先选择能满足题目约束的传统视觉、几何和标定方案；只有当类别语义、遮挡或外观变化确实需要时，才进入模型、数据集和部署路线。不要因为有现成模型就增加复杂度。
6. 用户已有工程、接线、协议、坐标系或下位机代码时，先阅读并保留已确认部分，只修改本次需求涉及的最小范围。不要擅自发明串口帧、ACK、心跳、坐标单位、频率或安全动作。
7. 如果题目明确由 MSPM0 或其他下位机负责巡迹、电机或安全控制，默认保留职责边界；RK3566 负责视觉、坐标/误差计算和已确认的接口，除非用户明确要求重分工。
8. 先完成相机采集、单帧算法、通信或执行机构的独立最小验证，再做闭环联调。每轮只改变一个主要变量。
9. 性能、帧率、延迟、精度、稳定运行时间和资源占用必须来自目标板实测。没有实测数据时标记为“待实测”，不能用桌面电脑结果代替。
10. 生成工程时只创建有真实职责的文件。默认从单一入口和最小目录开始；只有参数复用、模块边界、独立风险或测试需要时才拆分文件。板端路径使用项目相对路径，不依赖用户电脑绝对路径。
11. 题目、硬件、系统、API、版本或方案存在明显不确定性时，先按 `references/research-guidance.md` 形成研究卡；官方资料和原始题面用于确认事实，公开案例只用于补充路线和失败模式。
12. 高影响项未确认前，只能输出比较、假设和最小验证，不把候选协议、引脚、坐标、模型、工程结构或安全动作当成最终实现。
13. 区分 Codex 当前可访问的本地工作区和 VS Code Remote-SSH 连接的泰山派。若 Codex 没有远程终端权限，不得声称已经执行板端命令、读取板端日志或完成实板验证；应生成可复制命令，要求用户在 Remote-SSH 终端运行，并分析用户返回的输出或 JSON 证据。
14. 门禁为“部分通过”或“阻塞”时，只交付需求卡、信息缺口、方案边界和最小探测。不得确定设备号、引脚、协议、坐标、模型、性能数字或生成完整工程；合理假设必须附用途、影响和验证方法。

## 工作流

### 0. 执行首次使用门禁

读取 `templates/first-use-gate.md`，建立“已确认事实、用户选择、合理假设、待验证项”四类台账。基础必查板卡身份、系统/内核/架构、Codex 的板端可访问性和本次目标；摄像头、UART、GPIO、执行机构或模型只在题目/测试涉及它们时进入对应探测。

门禁结论只能是“通过、部分通过、阻塞”。部分通过只允许完成列出的最小验证；阻塞只输出缺口、低风险探测和需要用户确认的选择。用户只给陌生题面时，同时完成能从题面提取的需求卡，不等待所有信息齐全后才开始分析。

### 1. 建立题目约束卡

读取 `templates/task-intake.md`，提取目标、评分点、验收方式、场景、目标外观、允许硬件、执行机构、通信、安全限制和信息缺口。信息不足时先输出缺口和可选假设，不直接生成最终协议或完整闭环代码。

用户只请求一个低风险、范围明确的 API、命令、语法或单硬件测试时，读取 `templates/quick-check-intake.md`，完成轻量门禁后只输出自包含的探测/验证代码、预期现象、失败排查、证据保存和下一步，不启动完整方案矩阵。

### 2. 分类视觉任务

将题目归入一个主类型和必要的次类型，并读取匹配章节：颜色/几何与传统识别、静态测量、结构化标记/格点/路径、运动跟踪、多目标盘点、视觉控制或混合题型。说明分类依据、相机观测量、外部观测量和最终输出。不要把“识别到目标”直接等同于“已经完成定位、测量、跟踪或控制”。

### 3. 选择方案并写出降级路线

读取 `templates/solution-options.md`。只有存在真实取舍时才给出 2-3 个方案，否则给出一条推荐路线和被排除的路线。每个保留方案说明观测量、坐标系、标定/数据负担、板端依赖、最小验证、失败信号、降级方式和接口边界。

默认顺序是：能用稳定颜色/几何/标定解决就不引入模型；需要类别语义或复杂外观时再评估 OpenCV DNN、RKNN 或其他运行时。缺少授权模型、数据集或目标板实测时，标记阻塞项。

用户确认方案及高影响项前，等待选择，不直接生成完整闭环代码。需要通信时读取 `templates/serial-protocol-decision.md`，单独确认是否需要序号、ACK、心跳、重发和超时；不得因“常见做法”自动加入。

### 4. 发现板端运行环境

对于 VS Code Remote-SSH，用户在 VS Code 界面中编辑、编译、运行和查看日志，但所有文件、编译器、程序和日志位于泰山派 Linux。读取 `references/board-and-runtime.md`，先检查实际系统和能力，不把 ADB、scrcpy、VirtualBox 或 Docker 设为必需。

用户提供板端 JSON、日志或性能记录时，将其标为“当前用户环境的实测证据”；可以用来分析该环境和验证探针，但不能把其中的设备节点、分辨率、协议或性能数字推广为所有泰山派用户的默认配置。

先完成与当前任务有关的最小能力检查：系统/内核/架构和开发入口为基础项；图像任务检查摄像头与 OpenCV；涉及 UART/GPIO 时检查对应能力；只有使用用户已有模型的路线才检查目标模型运行时。工具不存在时给出替代检查，不伪造成功。

若当前 Codex 只连接用户电脑而不能访问 VS Code 的远程终端，则把探针当作用户执行的验证工件：给出工作目录、完整命令、预期输出、退出码和保存方式；用户执行后返回文本、JSON、日志或截图，才能更新平台事实。

### 5. 先交付最小验证

按“相机单帧采集 -> 单帧算法 -> 坐标/标定或跟踪状态 -> 独立通信/执行机构 -> 低速低风险闭环 -> 题目验收”顺序实现。每个验证程序说明硬件假设、预期现象、失败排查和下一步；API 未被当前环境确认时，先输出探测代码或命令。

### 6. 联调和故障排查

按“输入 -> 视觉 -> 坐标/状态 -> 通信 -> 执行 -> 反馈”的链路定位问题。记录原始帧/ROI、检测结果、时间戳、状态转换、发送帧和执行反馈；将“电脑上能看到”“程序输出了”“板端真实执行了”分开证明。

遇到低帧率、误检、抖动、丢目标、串口积压、模型失败或重启时，先给证据、可能瓶颈、低风险优化和回归测试，不直接改动高影响坐标、协议或安全参数。

用户提供已有工程时，先读取 `references/existing-project-integration.md` 和 `templates/existing-project-change.md`，读取相关源码/配置、建立基线并保留已确认接口；材料不足时只索取最小材料，不生成平行工程。需要记录“电脑看到、程序输出、板端执行、评分达成”的证据时，使用 `templates/debug-evidence.md`。

### 7. 形成可交付工程和验收报告

读取 `templates/project-architecture.md` 和 `templates/acceptance-checklist.md`。输出完整项目树、唯一入口、真实依赖、部署/运行方式、配置说明、最小测试和验收记录；不只给零散代码片段。

按 `references/validation-and-evidence.md` 区分采集帧率、视觉处理帧率、端到端延迟、误差、控制发布频率、连续运行时间和异常次数。没有目标板数据就保留“待实测”。

涉及模型时，读取 `templates/yolo-data-and-training.md`；涉及性能数字时，读取 `templates/performance-report.md`。

## 回答格式

涉及新题目或复杂改动时，按以下顺序回答：门禁结论；四类信息台账；视觉任务分类和推荐路线；坐标、标定、状态和接口边界；最小验证、预期证据与失败判据；降级路线；门禁通过后才提供工程结构与代码；验收指标与仍待实测内容。

用户只问一个低风险 API、命令或语法问题时，缩小范围，只给必要的探测/验证代码和边界，不强行启动完整方案选择流程。

修改首次门禁、题型选择或核心工作流后，按 `references/validation-scenarios.md` 执行 R1、R2、R3；其他修改至少执行一个匹配场景。若出现信息不足时擅自定协议、已有工程未先阅读、无数据集却声称模型可用或无实测却声称达标，不能发布该版本。

## 安全与发布边界

- 激光、云台、电机和无人机测试先使用低能量、限幅、急停或空载模式；涉及人眼、旋转机构、飞行器或高功率执行器时明确安全条件。
- 不把用户本地路径、账号、密钥、令牌、未授权模型、私有数据集或个人信息写入公开 Skill。
- 公开输出区分官方事实、共建案例、竞赛题目、用户经验和待验证结论，并保留来源链接。
- 不复制 MaixPy 或其他平台的专属 API；只迁移可泛化的方法，并按泰山派当前环境重新验证。
