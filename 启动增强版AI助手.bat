@echo off
chcp 65001 >nul
echo ========================================
echo 启动增强版AI助手
echo ========================================
echo.
echo 新功能特性：
echo ✅ 完全自主工作，不需要输入"继续"
echo ✅ 智能判断任务完成状态
echo ✅ 支持多步骤复杂任务
echo ✅ 实时流式反馈
echo ✅ 自动错误重试
echo ✅ 任务完成自动总结
echo.
echo 使用说明：
echo 1. 双击悬浮球打开对话窗口
echo 2. 输入任务描述（如："启动QQ"）
echo 3. AI会自动完成整个任务流程
echo 4. 不需要输入"继续"，AI会自主工作
echo.
echo 示例任务：
echo - 启动QQ
echo - 打开Chrome并搜索天气
echo - 打开记事本并输入Hello World
echo.
echo 按任意键启动AI助手...
pause >nul
echo.
echo 正在启动增强版AI助手...
python simple_start.py
