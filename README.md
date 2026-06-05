# 🎙️ Voice Wake — 离线语音助手

> 喊一声，电脑听你的——完全离线、无需VPN、开箱即用

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

**Voice Wake** 是一个运行在本地的 Windows 语音助手。基于 OpenAI Whisper 离线语音识别，可以：
- 🎯 **喊唤醒词唤醒**（默认"狗蛋"），说完自动把指令发到 AI 对话框
- 🖥️ **语音控制电脑**：打开应用、调音量、锁屏、截图、开关机
- 🔌 **完全离线**：模型下载一次后，不需要网络、不需要 VPN、不调任何付费 API
- 📦 **开箱即用**：`install.bat` → 等3分钟 → `start.bat`，完事

---

## 🎬 效果演示

```
你：     狗蛋 帮我查一下徐州天气
Voice Wake: [识别] 帮我查一下徐州天气 → 自动粘贴到WorkBuddy → 发送
AI回复：  徐州今天多云，31°C...

你：     狗蛋 打开QQ音乐
Voice Wake: [识别] 打开QQ音乐 → 启动QQ音乐
```

---

## 🚀 快速开始

### 前提条件
- Windows 10/11
- Python 3.10+
- 麦克风
- 首次安装需联网下载模型（~500MB）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Czy050412/voice-wake.git
cd voice-wake

# 2. 一键安装（创建虚拟环境、安装依赖、下载模型）
install.bat

# 3. 启动
start.bat
```

### 校准点击位置（首次使用）

```
calibrate.bat → 鼠标移到输入框 → 按F12 → 完成
```

---

## 🎯 默认命令

### 系统控制
| 命令 | 功能 |
|------|------|
| 打开 QQ音乐 / 微信 / 浏览器 | 启动应用 |
| 音量增大 / 减小 / 静音 | 音量控制 |
| 锁屏 | 锁定电脑 |
| 截图 | 截屏保存到桌面 |
| 关机 / 重启 / 睡眠 | 电源控制 |
| 现在几点 / 几号 / 电量 | 系统信息 |

### AI 对话
| 命令 | 功能 |
|------|------|
| 狗蛋 + 你的问题 | 自动发给 WorkBuddy / CodeBuddy |

> 系统命令和 AI 对话会自动分流——说"打开QQ音乐"会在本地执行，说"帮我写代码"会发给 AI。

---

## ⚙️ 配置

编辑 `config/settings.yaml` 即可自定义，不用改代码：

```yaml
wake_word: "狗蛋"        # 换成你喜欢的唤醒词
model: "small"           # tiny/small/medium/large（越大越准越慢）
commands:
  enabled: true          # 开关系统命令
workbuddy:
  enabled: true          # 开关 AI 对话功能
```

---

## 📁 项目结构

```
voice_wake/
├── voice_wake.py          # 核心引擎
├── commands/
│   └── voice_commands.py  # 系统命令插件
├── config/
│   └── settings.yaml      # 可视化配置
├── scripts/
│   ├── setup_autostart.bat # 开机自启
│   └── package.bat         # 打包分发
├── install.bat             # 一键安装
├── requirements.txt        # 依赖清单
└── calibrate.py            # 坐标校准工具
```

---

## 🔧 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 语音识别 | **faster-whisper** (OpenAI Whisper small) | 离线运行，CTranslate2 加速 |
| 音频采集 | **PyAudio** + SpeechRecognition | 麦克风 + VAD 语音活动检测 |
| 窗口自动化 | **pyautogui** + Win32 API | 点击输入框、粘贴、发送 |
| TTS 反馈 | **Windows SAPI** | 系统自带语音合成 |
| 配置系统 | **YAML** | 可视化参数调优 |

---

## 🤔 为什么用 faster-whisper 而不是 XXX？

| 方案 | 中文准确率 | 是否需要VPN | 模型大小 | 最终结论 |
|------|-----------|------------|---------|---------|
| Google API | ~85% | 必须 | 云端 | ❌ 依赖VPN |
| Vosk | ~60% | 不需要 | 42MB | ❌ 中文太差 |
| FunASR | 95%+ | 不需要 | 944MB | ❌ 国内下载超时 |
| **faster-whisper** | **~90%** | **不需要（运行后）** | **500MB** | ✅ **最佳平衡** |

---

## 🧩 扩展

### 添加自定义命令

在 `commands/` 目录下创建新的 Python 文件，实现 `execute_command(text)` 函数即可自动加载。

### 开机自启

```bash
scripts/setup_autostart.bat
```

### 打包分发

```bash
scripts/package.bat
# 生成 voice_wake_portable/ 文件夹，拷到U盘即用
```

---

## 📝 License

MIT — 随便用，随便改，随便分发。

---

## ☕ 打赏支持

如果这个项目对你有帮助，欢迎请我喝杯咖啡 ☕

<div align="center">
  <img src="assets/wechat-pay.png" alt="微信打赏" width="200">
  <br>
  <sub>微信扫一扫，支持开发者继续维护 ❤️</sub>
</div>

> 开源不易，你的每一份支持都是我继续迭代的动力！

---

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) — 语音识别模型
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 加速推理
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) — 音频采集库

---

**Made with ❤️ in Xuzhou, China**
