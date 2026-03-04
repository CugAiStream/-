@echo off
chcp 65001 >nul
REM 启动视频下载工具命令行版本

echo 启动视频下载工具命令行版本...
python video_downloader.py %*

pause
