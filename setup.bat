@echo off
chcp 65001 >nul 2>&1
title Voice Wake - 一键配置环境
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   Voice Wake v2.0 - 一键环境配置             ║
echo  ║   Windows 离线语音助手                        ║
echo  ╚══════════════════════════════════════════════╝
echo.

set "VENV_DIR=.venv"
set "REQUIREMENTS=requirements.txt"
set "FAILED=0"

:: ======================== Step 1: Check Python ========================
echo [1/6] 检测 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ╔══════════════════════════════════════════════╗
    echo  ║  ❌ 未检测到 Python！                         ║
    echo  ╠══════════════════════════════════════════════╣
    echo  ║  请按以下步骤手动安装：                       ║
    echo  ║                                              ║
    echo  ║  1. 访问 https://www.python.org/downloads/   ║
    echo  ║  2. 下载 Python 3.11+                        ║
    echo  ║  3. 安装时务必勾选 "Add Python to PATH"     ║
    echo  ║  4. 安装完成后重新运行此脚本                  ║
    echo  ╚══════════════════════════════════════════════╝
    echo.
    set "FAILED=1"
    goto :manual_guide
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo       ✅ Python %PYVER% 已安装

:: Check Python version >= 3.10
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo       ❌ Python 版本过低 (%PYVER%)，需要 3.10+
    echo       请访问 https://www.python.org/downloads/ 升级 Python
    set "FAILED=1"
    goto :manual_guide
)

:: ======================== Step 2: Create venv ========================
echo.
echo [2/6] 创建虚拟环境...
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo       ✅ 虚拟环境已存在，跳过创建
) else (
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo       ❌ 创建虚拟环境失败
        echo       请确认 Python 安装时勾选了 "pip" 和 "venv" 组件
        set "FAILED=1"
        goto :manual_guide
    )
    echo       ✅ 虚拟环境创建成功
)

:: ======================== Step 3: Upgrade pip ========================
echo.
echo [3/6] 升级 pip...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com >nul 2>&1
if errorlevel 1 (
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
)
echo       ✅ pip 已是最新版

:: ======================== Step 4: Install dependencies ========================
echo.
echo [4/6] 安装依赖包（可能需要几分钟）...
echo       尝试使用国内镜像源...

"%VENV_DIR%\Scripts\pip.exe" install -r "%REQUIREMENTS%" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
if errorlevel 1 (
    echo       ⚠️ 镜像源安装部分失败，尝试官方 PyPI...
    "%VENV_DIR%\Scripts\pip.exe" install -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo       ❌ 依赖安装失败
        set "FAILED=1"
        goto :manual_guide
    )
)
echo       ✅ 依赖包安装完成

:: ======================== Step 5: Download model ========================
echo.
echo [5/6] 下载语音识别模型（~500MB，仅首次）...
if exist ".whisper_cache\models--Systran--faster-whisper-small" (
    echo       ✅ 模型已存在，跳过下载
) else (
    "%VENV_DIR%\Scripts\python.exe" -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='.whisper_cache')"
    if errorlevel 1 (
        echo       ⚠️ 模型下载失败（可能是网络问题）
        echo       你可以稍后手动下载：
        echo       .venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='.whisper_cache')"
        echo       或者设置代理后重试：
        echo       set HTTPS_PROXY=http://127.0.0.1:7890
        echo       然后重新运行 setup.bat
        set "FAILED=1"
        goto :manual_guide
    )
    echo       ✅ 模型下载完成
)

:: ======================== Step 6: Create shortcut ========================
echo.
echo [6/6] 创建桌面快捷方式...
"%VENV_DIR%\Scripts\python.exe" create_shortcut.py >nul 2>&1
if errorlevel 1 (
    echo       ⚠️ 快捷方式创建失败，不影响使用
) else (
    echo       ✅ 桌面快捷方式已创建
)

:: ======================== Done ========================
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║  🎉 环境配置完成！                            ║
echo  ╠══════════════════════════════════════════════╣
echo  ║                                              ║
echo  ║  启动方式：                                   ║
echo  ║    双击 start.bat                            ║
echo  ║    或双击桌面 "Voice Wake" 快捷方式          ║
echo  ║                                              ║
echo  ║  首次使用建议：                               ║
echo  ║    运行 calibrate.bat 校准输入框位置          ║
echo  ║                                              ║
echo  ║  对着麦克风说 "狗蛋" 即可唤醒！              ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
exit /b 0

:: ======================== Manual Guide ========================
:manual_guide
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║  ⚠️ 一键配置失败，请按以下步骤手动配置：     ║
echo  ╠══════════════════════════════════════════════╣
echo  ║                                              ║
echo  ║  1. 确保已安装 Python 3.10+                   ║
echo  ║     https://www.python.org/downloads/         ║
echo  ║     安装时勾选 "Add Python to PATH"          ║
echo  ║                                              ║
echo  ║  2. 打开 cmd，进入项目目录                    ║
echo  ║     cd /d 你的路径\voice-wake                 ║
echo  ║                                              ║
echo  ║  3. 创建虚拟环境                             ║
echo  ║     python -m venv .venv                     ║
echo  ║                                              ║
echo  ║  4. 激活虚拟环境                             ║
echo  ║     .venv\Scripts\activate                   ║
echo  ║                                              ║
echo  ║  5. 安装依赖（国内镜像）                      ║
echo  ║     pip install -r requirements.txt ^         ║
echo  ║       -i https://mirrors.aliyun.com/pypi/simple/ ║
echo  ║       --trusted-host mirrors.aliyun.com       ║
echo  ║                                              ║
echo  ║  6. 下载语音模型                             ║
echo  ║     python -c "from faster_whisper import ^   ║
echo  ║       WhisperModel; WhisperModel('small', ^   ║
echo  ║       device='cpu', compute_type='int8', ^    ║
echo  ║       download_root='.whisper_cache')"        ║
echo  ║                                              ║
echo  ║  7. 创建快捷方式（可选）                      ║
echo  ║     python create_shortcut.py                ║
echo  ║                                              ║
echo  ║  8. 启动                                     ║
echo  ║     start.bat                                ║
echo  ║                                              ║
echo  ║  常见问题：                                   ║
echo  ║  - PyAudio 安装失败 → 安装 VS Build Tools    ║
echo  ║  - 模型下载超时 → 设置代理或用 VPN           ║
echo  ║  - python 不是命令 → 重装 Python 并加 PATH   ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
exit /b 1
