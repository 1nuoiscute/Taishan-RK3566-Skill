# 泰山派 RK3566 板端环境与运行时发现

本参考只规定发现顺序，不把某个镜像、摄像头、串口名、GPIO 数字或部署工具写死。优先适配 VS Code Remote-SSH：VS Code 是操作界面，代码、编译、运行和日志在泰山派 Linux 中完成。

## 1. 系统基线

先记录以下输出，并把事实与用户选择分开：

```bash
cat /etc/os-release 2>/dev/null || true
uname -a
uname -m
command -v python3 || true
command -v g++ || true
```

记录系统发行版、内核、架构、编译器、Python 和 C++ 版本。Android、Buildroot、Ubuntu、OpenKylin、OpenHarmony 或其他环境不能混写为同一套命令。

## 2. 摄像头能力

先确认镜像是否已提供摄像头驱动、设备节点和用户态工具：

```bash
ls -l /dev/video* /dev/media* 2>/dev/null || true
command -v v4l2-ctl && v4l2-ctl --list-devices || true
command -v media-ctl && media-ctl -p || true
```

若没有 `v4l2-ctl` 或 `media-ctl`，不要宣称摄像头不可用；可先用 OpenCV、已有示例或系统日志做最小采集测试。确认设备后再确定 OpenCV backend、分辨率、像素格式和帧率。

OpenCV 只在导入和采集成功后使用；不要把桌面电脑的 camera index、分辨率或 backend 直接复制到板端。最小验证应记录设备、打开方式、实际帧尺寸、采集是否阻塞、是否有花屏/曝光/颜色问题和连续运行时间。

## 3. OpenCV 与模型运行时

```bash
python3 - <<'PY'
try:
    import cv2
    print("opencv", cv2.__version__)
except Exception as exc:
    print("opencv unavailable:", exc)
PY

command -v rknn-toolkit2 || true
command -v rknn_server || true
find /usr /opt -maxdepth 3 -iname '*rknn*' 2>/dev/null | head -50
```

以上只用于探测，不假定命令一定存在。模型路线必须进一步确认模型格式、转换工具、运行时版本、输入布局、量化方式、输出解码和目标板实测延迟。缺少任一关键项时，先提供传统视觉降级路线或标记阻塞项。

## 4. GPIO、UART 和通信

```bash
command -v gpioinfo && gpioinfo || true
ls -l /dev/ttyS* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
dmesg | grep -Ei 'tty|uart|gpio|video|camera|v4l2' | tail -100 || true
```

优先使用当前系统的 libgpiod、设备树和用户已确认的接口。不要根据物理 40 针编号直接推导 Linux GPIO 数字；不要在未知波特率、校验、帧格式或安全动作时生成完整通信协议。

如果下位机负责巡迹、电机或安全控制，先保持职责边界：RK3566 输出已确认的视觉结果、坐标误差或状态，下位机执行已确认的控制逻辑。

## 5. Remote-SSH 运行约定

在 VS Code 中优先完成：打开泰山派上的项目目录；在 Remote-SSH 终端确认当前主机、路径、用户和权限；运行最小采集或算法验证；记录终端输出、日志和版本信息；逐步加入通信和执行机构。

ADB、scrcpy、VirtualBox、Docker 和离线打包是可选环境分支，不能覆盖用户已经确认的 Remote-SSH 工作流。
