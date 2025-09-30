@echo off
chcp 65001
echo ========================================
echo 桌面AI助手启动脚本
echo ========================================
echo.
echo 启动桌面AI助手...
echo.
echo 使用方法:
echo 1. 双击悬浮球打开对话窗口
echo 2. 输入您的需求开始对话
echo 3. 右键悬浮球查看更多功能
echo.
echo 按任意键启动助手...
pause >nul

echo 正在启动桌面AI助手...
python run_assistant.py
