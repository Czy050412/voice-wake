@echo off
title 学习报告6: 部署模式
echo [15:09] 学习进度: ~22分钟
echo.
echo 重大发现！ADLTX部署模式：
echo   第一次运行.bat做的事：
echo   把SaveGames(Liceing.sav+Save-FsLocation.sav)
echo   复制到User的AppData/Local目录
echo   这样首次启动就有授权+全屏配置！
echo.
echo 这就是零后端部署方案：
echo   1. 打包exe+pak
echo   2. 附带SaveGames(含授权+配置)
echo   3. bat脚本自动安装到用户目录
echo   4. 用户双击exe即可运行
echo   不需要服务器/注册/联网！
echo.
echo 两个存档文件：
echo   Liceing.sav = 授权许可
echo   Save-FsLocation.sav = 全屏位置
echo.
echo 离线授权模式可复用给Voice Wake!
echo   CDKEY写配置文件,启动检查->免费/Pro切换
pause