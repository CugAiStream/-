@echo off
chcp 65001 >nul
REM 测试视频下载工具绿色版的所有组件

setlocal enabledelayedexpansion

echo 开始测试视频下载工具绿色版的所有组件...
echo ================================

echo.
echo 1. 测试文件是否存在
set "files_to_check=video_downloader.py video_downloader_gui.py yt-dlp.exe ffmpeg.exe ffprobe.exe requirements.txt 安装依赖.bat 运行GUI.bat 运行命令行.bat"
set "missing_files="

for %%f in (%files_to_check%) do (
    if not exist "%%f" (
        set "missing_files=!missing_files! %%f"
    ) else (
        echo ✅ %%f 存在
    )
)

if not "!missing_files!" == "" (
    echo ❌ 缺少以下文件:!missing_files!
) else (
    echo ✅ 所有必要文件都存在
)

echo.
echo 2. 测试可执行文件版本

if exist "yt-dlp.exe" (
    echo 测试 yt-dlp 版本...
    yt-dlp.exe --version
    if %errorlevel% equ 0 (
        echo ✅ yt-dlp 版本测试成功
    ) else (
        echo ❌ yt-dlp 版本测试失败
    )
) else (
    echo ❌ yt-dlp.exe 不存在
)

echo.

if exist "ffmpeg.exe" (
    echo 测试 ffmpeg 版本...
    ffmpeg.exe -version
    if %errorlevel% equ 0 (
        echo ✅ ffmpeg 版本测试成功
    ) else (
        echo ❌ ffmpeg 版本测试失败
    )
) else (
    echo ❌ ffmpeg.exe 不存在
)

echo.
echo 3. 测试目录结构

if exist "downloads" (
    echo ✅ downloads 目录存在
) else (
    echo ⚠️ downloads 目录不存在，程序运行时会自动创建
)

if exist "converted" (
    echo ✅ converted 目录存在
) else (
    echo ⚠️ converted 目录不存在，程序运行时会自动创建
)

echo.
echo 4. 测试脚本内容

echo 检查 安装依赖.bat 内容...
type 安装依赖.bat
echo.

echo 检查 运行GUI.bat 内容...
type 运行GUI.bat
echo.

echo 检查 运行命令行.bat 内容...
type 运行命令行.bat
echo.

echo ================================
echo 测试完成！
echo ================================
echo.
echo 绿色版程序包包含所有必要的文件和组件。
echo 请按照以下步骤运行程序：
echo 1. 安装Python 3.6或更高版本
echo 2. 运行 "安装依赖.bat" 安装所需依赖
echo 3. 运行 "运行GUI.bat" 启动图形界面
echo 4. 或运行 "运行命令行.bat" 使用命令行模式

echo.
echo 注意：
echo - 下载国外视频网站可能需要代理
echo - 某些网站需要登录才能下载视频
echo - 请以管理员身份运行程序以获取Cookie权限
echo.
pause
