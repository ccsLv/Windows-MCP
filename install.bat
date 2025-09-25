@echo off
chcp 65001
echo ========================================
echo 桌面AI助手安装脚本
echo ========================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

echo 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 依赖包安装完成
echo.

echo 检查配置文件...
if not exist config.json (
    echo 创建默认配置文件...
    copy /y nul config.json >nul
    echo {> config.json
    echo     "api_key": "sk-ac3a4329ad1040228a0607564d13ac15",>> config.json
    echo     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",>> config.json
    echo     "model": "qwen-plus">> config.json
    echo }>> config.json
    echo 配置文件已创建
) else (
    echo 配置文件已存在
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 使用方法:
echo 1. 运行 run_assistant.py 启动助手
echo 2. 双击悬浮球打开对话窗口
echo 3. 输入您的需求开始对话
echo.
echo 按任意键启动助手...
pause >nul

echo 启动桌面AI助手...
python run_assistant.py
