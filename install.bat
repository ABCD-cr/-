@echo off
chcp 65001 >nul
echo ========================================
echo DeepSeek 自动答题系统 - 依赖安装
echo ========================================
echo.
echo 此脚本会自动安装程序运行所需的所有依赖库
echo.
pause

echo.
echo [1/2] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo.
    echo 错误：未找到 Python，请先安装 Python 3.7 或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/2] 安装依赖库...
echo.
echo 正在安装 openai（DeepSeek AI API）...
pip install openai>=1.0.0

echo.
echo 正在安装 pyautogui（自动化控制）...
pip install pyautogui>=0.9.54

echo.
echo 正在安装 pillow（图像处理）...
pip install pillow>=10.0.0

echo.
echo 正在安装 requests（HTTP 请求）...
pip install requests>=2.31.0

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 所有依赖库已成功安装，现在可以运行程序了


pause
