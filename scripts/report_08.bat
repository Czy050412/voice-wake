@echo off
title 学习报告8: 插件宝库
echo [15:12] ~14分钟
echo.
echo 你的百度网盘下载了超多UE5插件:
echo   1. Offline Speech Recognition (VoskPlugin v1.9)
echo      - UE5内嵌语音识别，C++插件
echo      - 支持Win64/Mac/Linux
echo      - 和我们Voice Wake不同路线:
echo        Voice Wake用Python打HTTP/操控窗口
echo        VoskPlugin在引擎内直接语音->蓝图事件
echo.
echo   2. ChunkCore Chunk Downloader
echo      - 分块下载/热更新专业插件
echo      - 支持5.1-5.7多个版本
echo      - 比引擎自带的ChunkDownloader更强大
echo.
echo   3. Blueprint Assist (v4.4.5)
echo      - 蓝图编辑器效率工具
echo      - 支持到5.6版本
echo.
echo   4. Darker Nodes / Electronic Nodes
echo      - 蓝图节点美化主题
echo.
echo 你的实验路径:
echo   UE5内嵌Vosk(引擎内识别) -> 放弃
echo   Python Voice Wake(引擎外识别) -> 成功
echo   最终绕过了UE5的限制!
pause