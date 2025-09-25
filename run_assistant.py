#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面AI助手启动脚本
"""

import sys
import os
import json
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'openai', 'pyautogui', 'pyperclip', 
        'requests', 'uiautomation', 'markdownify'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    # 单独检查tkinter
    try:
        import tkinter
    except ImportError:
        missing_packages.append('tkinter')
    
    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def load_config():
    """加载配置文件"""
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认配置
        return {
            "api_key": "sk-ac3a4329ad1040228a0607564d13ac15",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "ui": {
                "window_width": 400,
                "window_height": 500,
                "ball_size": 60,
                "ball_color": "#4A90E2",
                "ball_hover_color": "#357ABD",
                "chat_bg_color": "#F5F5F5",
                "user_bg_color": "#4A90E2",
                "ai_bg_color": "#FFFFFF",
                "font_family": "Microsoft YaHei UI",
                "font_size": 10
            }
        }

def main():
    """主函数"""
    print("=" * 50)
    print("桌面AI助手 - 基于Windows MCP和Qwen3")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return
    
    # 加载配置
    config = load_config()
    print(f"使用模型: {config['model']}")
    print(f"API地址: {config['base_url']}")
    
    # 导入并运行助手
    try:
        from desktop_assistant_mcp import FloatingBall, Config
        
        # 创建配置对象
        assistant_config = Config()
        assistant_config.api_key = config['api_key']
        assistant_config.base_url = config['base_url']
        assistant_config.model = config['model']
        
        # 更新UI配置
        ui_config = config.get('ui', {})
        for key, value in ui_config.items():
            if hasattr(assistant_config, key):
                setattr(assistant_config, key, value)
        
        print("\n启动悬浮球AI助手...")
        print("双击悬浮球打开对话窗口")
        print("拖拽悬浮球可以移动位置")
        print("按Ctrl+C退出程序")
        
        # 创建并运行悬浮球
        ball = FloatingBall(assistant_config)
        
        # 异步初始化MCP连接
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if loop.run_until_complete(ball.initialize()):
                print("MCP连接初始化成功")
                ball.run()
            else:
                print("MCP连接初始化失败")
        finally:
            loop.close()
        
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保所有依赖包已正确安装")
    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
