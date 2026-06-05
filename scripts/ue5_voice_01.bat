@echo off
title UE5内嵌Voice 完整方案
echo [15:22]
echo.
echo ==========================================
echo   UE5内嵌Voice - 三种方案对比
echo ==========================================
echo.
echo [方案A] VoskPlugin(你已下载)
echo   优点: 全蓝图,引擎内运行
echo   缺点: 中文识别差(我们验证过)
echo   结论: 不推荐用于中文
echo.
echo [方案B] HTTP桥接(推荐!)
echo   架构: voice_server.py在后台
echo         UE5通过VaRest发WAV字节到localhost:9876
echo         返回识别文本到蓝图
echo   优点: 用faster-whisper(中文准)
echo         纯蓝图对接(你已有VaRest!)
echo   缺点: 需要voice_server.py后台运行
echo.
echo [方案C] 外部进程
echo   架构: UE5用jsPlugins/ExecuteProcess
echo         启动voice_server.py为子进程
echo   优点: 零手动启动, 一体化体验
echo   缺点: 需要管理进程生命周期
echo.
echo ==========================================
echo   推荐方案B: 两步集成(15分钟搞定)
echo ==========================================
echo.
echo 步骤1: 启动voice_server.py
echo   双击 voice_server_start.bat
echo   -> localhost:9876 就绪
echo.
echo 步骤2: UE5蓝图连线
echo   打开CIM的UI蓝图
echo   添加 VaRest 节点:
echo     ConstructVaRestRequestExt(Verb=POST)
echo     -> SetURL(http://127.0.0.1:9876/recognize)
echo     -> SetBinaryRequestContent(WAV数据)
echo     -> ExecuteProcessRequest
echo   OnComplete:
echo     -> GetResponseContentAsString
echo     -> 解析JSON的text字段
echo     -> 匹配命令 -> 触发按钮事件
echo.
echo 步骤3: 测试
echo   用浏览器POST测试 -> 蓝图对接 -> 喊命令
pause