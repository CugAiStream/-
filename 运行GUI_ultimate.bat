@echo off
chcp 65001 >nul
title 视频下载和编解码工具 - 终极改进版

echo ========================================
echo   视频下载和编解码工具 - 终极改进版
echo ========================================
echo.

REM 检测Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python安装！
    echo.
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [信息] Python已安装
python --version
echo.

REM 检测依赖是否已安装
echo [信息] 检查依赖...
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] tkinter可能未正确安装
)

REM 创建必要的目录
if not exist "downloads" mkdir downloads
if not exist "converted" mkdir converted
if not exist "logs" mkdir logs

echo.
echo [信息] 启动终极改进版GUI...
echo.
echo 提示:
echo - 日志文件会自动保存在 logs/ 目录
echo - 下载的视频保存在 downloads/ 目录
echo - 转换后的视频保存在 converted/ 目录
echo.
echo 按任意键启动...
pause >nul

REM 启动终极改进版GUI
python video_downloader_ultimate.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序异常退出，错误代码: %errorlevel%
    echo.
    pause
)
