@echo off
echo 正在启动视频下载工具...
echo.

REM 检查Python是否存在
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo 使用系统Python
    python video_downloader_final.py
) else (
    echo 系统Python未找到，尝试使用其他Python安装
    
    REM 尝试常见的Python路径
    if exist "C:\Python39\python.exe" (
        echo 使用 C:\Python39\python.exe
        "C:\Python39\python.exe" video_downloader_final.py
    ) else if exist "C:\Python38\python.exe" (
        echo 使用 C:\Python38\python.exe
        "C:\Python38\python.exe" video_downloader_final.py
    ) else if exist "C:\Python37\python.exe" (
        echo 使用 C:\Python37\python.exe
        "C:\Python37\python.exe" video_downloader_final.py
    ) else if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python39\python.exe" (
        echo 使用用户目录Python39
        "%USERPROFILE%\AppData\Local\Programs\Python\Python39\python.exe" video_downloader_final.py
    ) else if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python38\python.exe" (
        echo 使用用户目录Python38
        "%USERPROFILE%\AppData\Local\Programs\Python\Python38\python.exe" video_downloader_final.py
    ) else (
        echo 错误: 未找到Python安装
        echo 请先安装Python 3.7或更高版本
        echo 可以从 https://www.python.org/downloads/ 下载
        pause
    )
)

echo.
echo 程序已退出
pause