# 🎙️ Voice Wake v2.0 — 离线语音助手

> 喊一声，电脑听你的——完全离线、无需VPN、开箱即用

[![Version](https://img.shields.io/badge/Version-2.0-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()
[![Stars](https://img.shields.io/github/stars/Czy050412/voice-wake?style=social)](https://github.com/Czy050412/voice-wake)

**Voice Wake** 是一个运行在本地的 Windows 语音助手。基于 OpenAI Whisper 离线语音识别，可以：
- 🎯 **喊唤醒词唤醒**（默认"狗蛋"），说完自动把指令发到 AI 对话框
- 🖥️ **语音控制电脑**：打开应用、调音量、锁屏、截图、开关机
- 📺 **语音可视化浮窗**：双屏透明HUD，实时显示识别状态
- 🔌 **完全离线**：模型下载一次后，不需要网络、不需要 VPN、不调任何付费 API
- 📦 **开箱即用**：`setup.bat` → 等3分钟 → `start.bat`，完事

---

## 🆕 v2.0 新特性

| 特性 | 说明 |
|------|------|
| 🎙️ **faster-whisper 引擎** | 替代 Google API，完全离线，CTranslate2 加速，中文识别 ~90% |
| 📺 **语音可视化浮窗** | 透明HUD浮窗，实时显示识别状态，支持双屏定位 |
| 🖱️ **点击穿透** | 浮窗不阻挡鼠标操作，纯看模式 |
| 🔒 **单实例保护** | PID锁文件，防止重复启动产生多个窗口 |
| ⚡ **参数调优** | energy_threshold=550, pause_threshold=0.6, dynamic_energy=False |
| 🛑 **一键启停** | start.bat / stop.bat，桌面快捷方式 |
| 🔧 **一键配置环境** | setup.bat 自动检测并安装所有依赖 |

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

## 💻 系统要求

### 必须满足

| 要求 | 最低版本 | 说明 |
|------|---------|------|
| **操作系统** | Windows 10 1809+ | 依赖 Win32 API（DPI感知、分层窗口、点击穿透） |
| **Python** | 3.10+ | 推荐 3.11 或 3.12（3.13 也兼容） |
| **内存** | 4 GB+ | faster-whisper small 模型运行需要约 1.5 GB |
| **磁盘** | 2 GB+ | 模型文件 ~500MB + 依赖包 ~800MB |
| **麦克风** | 任意 | USB/3.5mm/蓝牙均可，需要能在 Windows 中被识别 |
| **网络** | 首次安装时需要 | 下载模型和依赖（安装完成后完全离线运行） |

### 可选

| 组件 | 说明 |
|------|------|
| **双显示器** | 浮窗默认显示在第二块屏幕左上角；单屏则显示在主屏左上角 |
| **WorkBuddy / CodeBuddy** | 安装后语音指令可自动粘贴到 AI 对话框并发送 |
| **GPU (CUDA)** | 当前版本使用 CPU int8 推理，GPU 支持计划中 |

### Python 依赖项

| 包名 | 版本要求 | 用途 |
|------|---------|------|
| `faster-whisper` | >=1.0.0 | 离线语音识别引擎（CTranslate2 加速） |
| `SpeechRecognition` | >=3.10.0 | 麦克风音频采集 + VAD |
| `PyAudio` | >=0.2.11 | 音频设备接口（PortAudio 封装） |
| `Pillow` | >=10.0.0 | 浮窗文字渲染（RGBA 透明图像） |
| `pyautogui` | >=0.9.0 | 窗口自动化（点击、粘贴、发送） |
| `pyperclip` | >=1.8.0 | 剪贴板操作 |
| `pywin32` | >=300 | Win32 API 调用（窗口管理、快捷方式） |
| `pyyaml` | >=6.0.0 | 配置文件解析 |

> 以上依赖全部由 `setup.bat` 自动安装，你不需要手动 `pip install` 任何东西。

---

## 🚀 快速开始（开箱即用）

### Step 1：安装 Python

如果你还没装 Python：
1. 前往 [python.org](https://www.python.org/downloads/) 下载 Python 3.11+
2. 安装时**务必勾选** ✅ "Add Python to PATH"
3. 安装完成后打开 cmd 运行 `python --version` 确认

### Step 2：克隆仓库

```bash
git clone https://github.com/Czy050412/voice-wake.git
cd voice-wake
```

或者直接下载 ZIP 解压。

### Step 3：一键配置环境

```bash
setup.bat
```

这个脚本会自动完成：
1. ✅ 检测 Python 是否安装及版本
2. ✅ 创建虚拟环境 `.venv`
3. ✅ 升级 pip 到最新版
4. ✅ 安装所有依赖包（优先用国内镜像源，失败则回退官方源）
5. ✅ 下载 faster-whisper small 模型（~500MB，一次性）
6. ✅ 创建桌面快捷方式

> ⚠️ 如果 `setup.bat` 失败，请看下方 [手动配置](#-手动配置环境) 章节。

### Step 4：启动

```bash
start.bat
```

或者双击桌面上的 **Voice Wake** 快捷方式。

### Step 5：校准（首次使用）

如果你的 WorkBuddy 输入框位置不对，运行一次校准：

```bash
calibrate.bat
```

把鼠标移到 AI 对话输入框上，按 **F12** 保存坐标。

### 🎉 完成！

对着麦克风说 **"狗蛋"**，然后说你的指令。

---

## 🔧 手动配置环境

如果 `setup.bat` 一键配置失败（网络问题、权限问题等），可以手动操作：

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
.venv\Scripts\activate

# 3. 升级 pip
python -m pip install --upgrade pip

# 4. 安装依赖（国内镜像源）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 如果镜像源失败，用官方源
pip install -r requirements.txt

# 5. 下载语音模型
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='.whisper_cache')"

# 6. 创建桌面快捷方式（可选）
python create_shortcut.py
```

### 常见安装问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| `PyAudio` 安装失败 | 缺少 C++ 编译工具 | 安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)，或 `pip install pipwin && pipwin install pyaudio` |
| 模型下载超时 | HuggingFace 在国内访问慢 | 设置代理 `set HTTPS_PROXY=http://127.0.0.1:7890` 后重试，或手动下载模型放到 `.whisper_cache/` |
| `python` 不是内部命令 | Python 未加入 PATH | 重新安装 Python 勾选 "Add to PATH"，或手动添加环境变量 |
| 权限被拒绝 | 杀毒软件拦截 | 将项目目录加入杀毒软件白名单 |
| 虚拟环境创建失败 | Python 安装不完整 | 卸载重装 Python，确保勾选 "pip" 和 "venv" 组件 |

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
# --- 核心设置 ---
wake_word: "狗蛋"            # 换成你喜欢的唤醒词
language: "zh"              # 识别语言
model: "small"              # tiny/small/medium/large（越大越准越慢）

# --- WorkBuddy 集成 ---
workbuddy:
  enabled: true             # 开关 AI 对话功能
  input_offset_y: -180      # 输入框位置偏移（像素）

# --- 系统命令 ---
commands:
  enabled: true             # 开关系统命令

# --- 语音反馈 ---
tts:
  enabled: true             # 开关语音回复
  voice: "default"          # Windows SAPI 语音名
  rate: 0                   # 语速 (-10 到 10)

# --- 高级参数 ---
advanced:
  mic_index: null           # null=自动检测，或指定麦克风索引号
  energy_threshold: 550     # 麦克风灵敏度（越大越不容易误触发，推荐 400-800）
  pause_threshold: 0.6      # 说完多久算一句（秒，越小响应越快，推荐 0.5-1.0）
  phrase_limit: 10          # 最长录音时间（秒）
  send_cooldown: 3.0        # 发送间隔（秒）
  dynamic_energy: false     # 自动调节灵敏度（⚠️ 建议关闭，会导致越来越灵敏）
  silence_threshold: 300    # 静音检测阈值
```

### 参数调优指南

| 参数 | 问题 | 调整建议 |
|------|------|---------|
| `energy_threshold` | 旁边有人说话就误触发 | 调大（600-1000） |
| `energy_threshold` | 说话不触发 | 调小（300-400） |
| `pause_threshold` | 说完等太久才响应 | 调小（0.4-0.5） |
| `pause_threshold` | 话没说完就截断了 | 调大（0.8-1.2） |
| `dynamic_energy` | 越用越灵敏 | 关闭 `false` |
| `phrase_limit` | 录音时间太长/太短 | 按需调整（5-15秒） |

---

## 📺 语音浮窗

Voice Wake v2.0 新增透明浮窗，实时显示语音识别状态：

- **位置**：第二块屏幕左上角（单屏则在主屏左上角）
- **尺寸**：1020 × 100 像素
- **透明背景**：PIL RGBA 渲染 + tkinter transparentcolor，文字悬浮无底色
- **点击穿透**：WS_EX_TRANSPARENT，不影响鼠标操作
- **常驻显示**：待机时显示"语音待机中..."，有语音事件时切换
- **自动回待机**：10秒无更新后回到待机状态

### 状态显示

| 状态 | 显示内容 | 颜色 |
|------|---------|------|
| 待机 | 语音待机中... / 说"狗蛋"唤醒 | 白色（暗） |
| 收听 | 正在收听... | 白色（灰） |
| 识别 | 识别到的文字 | 白色（亮） |
| 唤醒 | 狗蛋 > 请说话... | 绿色 |
| 发送 | 发送: xxx | 绿色 |
| 命令 | 系统命令执行结果 | 白色 |

---

## 📁 项目结构

```
voice-wake/
├── voice_wake.py           # 核心引擎（faster-whisper + 语音路由 + WorkBuddy集成）
├── voice_overlay.py        # 透明浮窗 HUD（PIL + tkinter + Win32 API）
├── voice_server.py         # UE5 HTTP 桥接服务（port 9876）
├── commands/
│   └── voice_commands.py   # 系统命令插件（音量/锁屏/截图/开关机等）
├── config/
│   └── settings.yaml       # 可视化配置文件
├── setup.bat               # 一键配置环境（创建venv + 安装依赖 + 下载模型）
├── start.bat               # 一键启动（自动杀旧进程 + 启动 overlay + 启动引擎）
├── stop.bat                # 一键停止（杀掉所有相关进程）
├── install.bat             # 旧版安装脚本（兼容保留）
├── calibrate.bat           # 坐标校准（首次使用需运行一次）
├── calibrate.py            # 校准工具代码
├── create_shortcut.py      # 创建桌面快捷方式
├── voice_server_start.bat  # UE5 HTTP服务启动脚本
├── download_funasr_hf.py   # FunASR 模型下载工具（备用）
├── download_funasr_model.py# FunASR 模型下载工具（备用）
├── requirements.txt        # Python 依赖清单
└── .gitignore              # Git 忽略规则
```

---

## 🔧 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 语音识别 | **faster-whisper** (OpenAI Whisper small) | 离线运行，CTranslate2 int8 加速，~90% 中文准确率 |
| 音频采集 | **PyAudio** + SpeechRecognition | 麦克风 + VAD 语音活动检测 |
| 语音浮窗 | **Pillow** + tkinter + Win32 API | RGBA透明渲染 + 点击穿透 + 双屏定位 + DPI感知 |
| 窗口自动化 | **pyautogui** + Win32 API | 查找窗口、点击输入框、粘贴、发送 |
| TTS 反馈 | **Windows SAPI** | 系统自带语音合成，零额外依赖 |
| 配置系统 | **PyYAML** | 人类可读的参数配置 |

---

## 🤔 为什么用 faster-whisper？

| 方案 | 中文准确率 | 是否需要VPN | 模型大小 | 最终结论 |
|------|-----------|------------|---------|---------|
| Google API | ~85% | 必须 | 云端 | ❌ 依赖VPN |
| Vosk | ~60% | 不需要 | 42MB | ❌ 中文太差 |
| FunASR | 95%+ | 不需要 | 944MB | ❌ 国内下载超时 |
| **faster-whisper** | **~90%** | **不需要（运行后）** | **500MB** | ✅ **最佳平衡** |

---

## 🧩 扩展

### 添加自定义命令

在 `commands/` 目录下创建新的 Python 文件，实现 `execute_command(text)` 函数即可自动加载：

```python
# commands/my_commands.py
def execute_command(text):
    """自定义命令处理器"""
    if "自定义关键词" in text:
        # 执行你的逻辑
        return ("my_command", True, "执行成功")
    return None
```

### UE5 集成

Voice Wake 提供 HTTP 桥接服务，可在 UE5 蓝图中通过 VaRest 调用：

```bash
voice_server_start.bat    # 启动 HTTP 服务 (port 9876)
# POST http://localhost:9876/recognize → {"text": "识别结果"}
```

---

## ❓ 常见问题 (FAQ)

### Q: 语音识别很慢怎么办？
调整 `config/settings.yaml`：
- `model` 改为 `"tiny"` 或 `"base"`（牺牲准确率换速度）
- `pause_threshold` 调小（如 0.4）

### Q: 旁边人说话会误触发？
- `energy_threshold` 调大（如 700-1000）
- 确保 `dynamic_energy: false`

### Q: 浮窗看不到？
- 检查是否在第二块屏幕上
- 确认 `voice_overlay.py` 进程在运行（`tasklist | findstr python`）
- 如果看不到但进程在，可能是 DPI 缩放问题，尝试重启

### Q: 浮窗颜色不对/有锯齿？
- 这是 `-transparentcolor` 的已知限制（抗锯齿像素被吃掉）
- 当前方案是最稳定的 tkinter 实现方式

### Q: 说"狗蛋"没反应？
- 检查麦克风是否正常工作（Windows 设置 → 声音）
- 调低 `energy_threshold`（如 300-400）
- 确认 `voice_wake.py` 进程在运行

### Q: 不想叫"狗蛋"怎么办？
编辑 `config/settings.yaml`，把 `wake_word` 改成你喜欢的词，比如 `"小爱"` 或 `"贾维斯"`。

---

## 📝 更新日志

### v2.0 (2026-06-05)
- 🎙️ 识别引擎从 Google API 升级到 faster-whisper（完全离线）
- 📺 新增语音可视化浮窗（透明HUD + 双屏 + 点击穿透）
- ⚡ 参数调优：energy_threshold=550, pause_threshold=0.6, dynamic_energy=False
- 🔒 单实例保护（PID锁文件）
- 🛑 一键启停脚本 + 桌面快捷方式
- 🔧 一键环境配置脚本（setup.bat）
- 🧩 UE5 HTTP 桥接服务
- 📦 项目模块化重构

### v1.0
- 初始版本（Google Speech API + 基础唤醒）

---

## 📝 License

MIT — 随便用，随便改，随便分发。

---

## 🎁 赞助支持

如果这个项目帮到了你，欢迎请我喝杯咖啡 ☕

> 💡 也欢迎 [点个 Star ⭐](https://github.com/Czy050412/voice-wake) — 这是最好的支持！

---

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) — 语音识别模型
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 加速推理
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) — 音频采集库
- [Pillow](https://python-pillow.org/) — 图像渲染库

---

**Made with ❤️ in Xuzhou, China**
