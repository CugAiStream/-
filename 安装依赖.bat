@echo off
chcp 65001 >nul
REM 安装视频下载工具的所有依赖

echo 开始安装依赖...
echo 执行命令: pip install -r requirements.txt

pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo 依赖安装成功！
    echo 现在可以运行 "运行GUI.bat" 或 "运行命令行.bat" 启动程序
) else (
    echo 依赖安装失败！
    echo 请检查网络连接，或手动运行: pip install -r requirements.txt
)

pause
