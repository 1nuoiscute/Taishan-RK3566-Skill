# 泰山派 RK3566 Skill 资料索引

本文件记录 Skill 设计阶段已经确认的公开资料和用户提供资料。原始 PDF、图片和网页内容不直接复制进公开仓库；发布时保留来源链接和必要的摘要，避免资料重复、版本过期或版权边界不清。

## 1. 设计参考

- MaixCAM Skill：`git@github.com:LanHua01/MaixCAM-skill.git`
- 参考作用：借鉴“赛题约束分析 -> 方案选择 -> 工程实现 -> 调试 -> 验收”的工作流，不复制 MaixPy、MaixVision 或 MaixCAM 专属 API。

## 2. 泰山派硬件资料

- 官方资料总入口：https://wiki.lckfb.com/zh-hans/tspi-rk3566/
- 官方下载中心：https://wiki.lckfb.com/zh-hans/tspi-rk3566/download-center.html
- 开源硬件项目：https://oshwhub.com/li-chuang-kai-fa-ban/li-chuang-tai-shan-pai-kai-fa-ban
- 用户提供原理图：`09_立创·泰山派开发板原理图.pdf`
- 用户提供官方 IO 分配表：两张 40 针接口和复用功能图片

已确认的硬件主题：RK3566 电源与地、LPDDR4、eMMC、USB、调试接口、CSI 摄像头、MIPI 屏幕与触摸、HDMI、eDP、Wi-Fi/蓝牙、TF 卡、音频、GPIO、按键和 RGB。

IO 资料的关键规则：

- 40 针编号、`GPIOx_y` 名称和复用功能必须分别记录。
- 复用功能不能同时使用，必须结合 Pinmux 和设备树确认。
- 不根据 `GPIOx_y` 名称直接臆测 Linux `gpio` 数字；必须以当前内核和设备树为准。
- 3.3 V、5 V 和 GND 引脚不是 GPIO。

## 3. 系统、编译和工具资料

以下页面来自立创泰山派官方 Wiki，Skill 应按用户实际环境选择，不把任何一种环境设为唯一前置条件。

### 系统与 SDK

- Android 系统使用：https://wiki.lckfb.com/zh-hans/tspi-rk3566/system-usage/android-system-usage.html
- Buildroot 系统使用：https://wiki.lckfb.com/zh-hans/tspi-rk3566/system-usage/buildroot-system-usage.html
- Linux SDK 编译：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/linux-compilation.html
- Kernel 6.1 Linux 编译：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/kernel6-1-linux-compilation.html
- Android SDK 编译：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/android-sdk-compilation.html
- Android 13 SDK 编译：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/android-13-sdk-compilation.html
- OpenKylin SDK 编译：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/openkylin-sdk-compilation.html
- OpenHarmony SDK 编译：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/openharmony-sdk-compilation.html
- Docker 编译环境：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/docker-compiling-environment.html
- VirtualBox Ubuntu 编译环境：https://wiki.lckfb.com/zh-hans/tspi-rk3566/sdk-compilation/virtualBox-ubuntu-compiling-environment.html

### 调试和工具

- ADB 安装和使用：https://wiki.lckfb.com/zh-hans/tspi-rk3566/tool-use/adb-install-use.html
- 调试工具：https://wiki.lckfb.com/zh-hans/tspi-rk3566/tool-use/debug-tools-use.html
- scrcpy：https://wiki.lckfb.com/zh-hans/tspi-rk3566/tool-use/scrcpy-tool-use.html

用户实际开发方式：VS Code + Remote-SSH 直接连接泰山派，在 VS Code 界面中完成编辑、编译、运行和日志查看。代码、编译器、程序和日志位于泰山派 Linux 环境中。ADB、scrcpy、VirtualBox、Docker 等应作为可选分支。

## 4. OpenCV 资料

以下页面在官方 Wiki 中标记为“共建”，可作为实践案例，不直接等同于官方 API、统一镜像能力或性能保证。

- 树莓派系统移植运行 OpenCV：https://wiki.lckfb.com/zh-hans/tspi-rk3566/documentation/gj-porting-raspberrypi-to-opencv.html
- Ubuntu 安装 OpenCV：https://wiki.lckfb.com/zh-hans/tspi-rk3566/documentation/gj-ubuntu-install-opencv.html
- OpenCV 人脸识别：https://wiki.lckfb.com/zh-hans/tspi-rk3566/documentation/gj-opencv-face-recognition.html
- Haar 级联 + LBPH：https://wiki.lckfb.com/zh-hans/tspi-rk3566/documentation/gj-opencv-face-recognition-haar-lpbh.html

摄像头采集接口暂不写死。不同镜像可能已经包含摄像头支持，Skill 应先检查实际镜像中的设备节点、V4L2/OpenCV 后端和可用工具，再进入算法实现。

## 5. 竞赛题目案例

### 2025 年 E 题：简易自行瞄准装置

- 用户提供本地资料：`docs/E题_简易自行瞄准装置.pdf`
- 视觉子任务：靶纸识别、靶心定位、二维云台瞄准、移动期间连续激光和圆弧同步。
- 关键约束：2 秒/4 秒内瞄准，`D1 <= 2 cm`；半径 6 cm 圆弧同步，`D2 <= 2 cm`，同步误差小于四分之一圈。
- 系统边界：巡迹和电机控制由 MSPM0 负责；RK3566 侧重点为视觉、几何误差和瞄准模块接口。

### 2025 年 C 题：基于单目视觉的目标物测量装置

- 页面：https://res.nuedc-training.com.cn/topic/2025/topic_122.html
- 视觉类型：静态目标的单目测量、标定、尺寸/距离计算和误差验收。

### 2023 年题：运动目标控制与自动追踪系统

- 页面：https://res.nuedc-training.com.cn/topic/2023/topic_99.html
- 视觉类型：运动目标检测、实时跟踪、控制闭环、目标丢失和重新捕获。

### 2024 年题：立体货架盘点无人机系统

- 页面：https://res.nuedc-training.com.cn/topic/2024/topic_112.html
- 视觉类型：空间场景、多目标盘点、视角变化、位置/距离估计，以及视觉与运动平台协同。

## 6. Skill 目标边界

Skill 面向公开使用者，目标是帮助使用泰山派 RK3566 参加电赛视觉类题目，形成可迁移的方法：

1. 从赛题提取目标、场景、评分、时限和安全约束。
2. 在传统视觉、几何测量、目标跟踪和模型推理之间选择路线。
3. 设计相机、坐标系、标定、误差和控制接口。
4. 在 VS Code Remote-SSH 或其他用户环境中完成板端验证。
5. 先做最小可验证模块，再进行视觉、通信和执行机构的闭环联调。
6. 用题目指标记录时间、误差、帧率、丢失率和降级行为。

不绑定某个用户的摄像头、镜像、串口协议、下位机、模型或固定题目。
