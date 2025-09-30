#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面AI助手启动器
提供悬浮球界面和对话功能
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import pyautogui
import pyperclip
import requests
from src.desktop import Desktop

class DesktopAIAssistant:
    def __init__(self):
        self.desktop = Desktop()
        self.config = self.load_config()
        self.root = None
        self.chat_window = None
        self.is_running = False
        
    def load_config(self):
        """加载配置文件"""
        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"配置文件加载失败: {e}")
        
        # 默认配置
        return {
            "api_key": "sk-ac3a4329ad1040228a0607564d13ac15",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus"
        }
    
    def create_floating_button(self):
        """创建悬浮球按钮"""
        self.root = tk.Tk()
        self.root.title("AI助手")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # 设置窗口大小和位置
        self.root.geometry("60x60+50+50")
        
        # 创建悬浮球按钮
        self.floating_btn = tk.Button(
            self.root,
            text="AI",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="raised",
            bd=2,
            command=self.open_chat_window
        )
        self.floating_btn.pack(fill=tk.BOTH, expand=True)
        
        # 绑定拖拽事件
        self.floating_btn.bind("<Button-1>", self.start_drag)
        self.floating_btn.bind("<B1-Motion>", self.drag_window)
        
        # 右键菜单
        self.create_context_menu()
        
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="打开对话", command=self.open_chat_window)
        self.context_menu.add_command(label="桌面状态", command=self.show_desktop_state)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="退出", command=self.quit_app)
        
        self.root.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def start_drag(self, event):
        """开始拖拽"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def drag_window(self, event):
        """拖拽窗口"""
        x = self.root.winfo_x() + (event.x - self.drag_start_x)
        y = self.root.winfo_y() + (event.y - self.drag_start_y)
        self.root.geometry(f"+{x}+{y}")
    
    def open_chat_window(self):
        """打开对话窗口"""
        if self.chat_window is None or not self.chat_window.winfo_exists():
            self.create_chat_window()
        else:
            self.chat_window.lift()
            self.chat_window.focus()
    
    def create_chat_window(self):
        """创建对话窗口"""
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("AI助手对话")
        self.chat_window.geometry("500x600+100+100")
        self.chat_window.attributes('-topmost', True)
        
        # 创建主框架
        main_frame = ttk.Frame(self.chat_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            height=20,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Microsoft YaHei", 10)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 输入框架
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输入框
        self.input_entry = tk.Entry(
            input_frame,
            font=("Microsoft YaHei", 10)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)
        
        # 发送按钮
        send_btn = ttk.Button(
            input_frame,
            text="发送",
            command=self.send_message
        )
        send_btn.pack(side=tk.RIGHT)
        
        # 功能按钮框架
        func_frame = ttk.Frame(main_frame)
        func_frame.pack(fill=tk.X)
        
        # 功能按钮
        ttk.Button(func_frame, text="桌面状态", command=self.show_desktop_state).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(func_frame, text="清空对话", command=self.clear_chat).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(func_frame, text="最小化", command=self.minimize_chat).pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定窗口关闭事件
        self.chat_window.protocol("WM_DELETE_WINDOW", self.close_chat_window)
        
        # 添加欢迎消息
        self.add_message("AI助手", "您好！我是桌面AI助手，可以帮您控制Windows系统。请告诉我您需要什么帮助。")
    
    def close_chat_window(self):
        """关闭对话窗口"""
        self.chat_window.destroy()
        self.chat_window = None
    
    def minimize_chat(self):
        """最小化对话窗口"""
        self.chat_window.iconify()
    
    def add_message(self, sender, message):
        """添加消息到聊天显示区域"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def clear_chat(self):
        """清空对话"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.add_message("AI助手", "对话已清空。")
    
    def send_message(self, event=None):
        """发送消息"""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        # 清空输入框
        self.input_entry.delete(0, tk.END)
        
        # 显示用户消息
        self.add_message("您", message)
        
        # 处理消息
        self.process_message(message)
    
    def process_message(self, message):
        """处理用户消息"""
        try:
            # 简单的命令处理
            if "桌面状态" in message or "状态" in message:
                self.show_desktop_state()
            elif "帮助" in message or "功能" in message:
                self.show_help()
            elif "退出" in message or "关闭" in message:
                self.quit_app()
            else:
                # 这里可以集成AI API调用
                self.add_message("AI助手", f"收到您的消息：{message}\n我正在处理中...")
                # 模拟AI响应
                threading.Timer(1.0, self.simulate_ai_response, args=(message,)).start()
        except Exception as e:
            self.add_message("AI助手", f"处理消息时出错：{str(e)}")
    
    def simulate_ai_response(self, message):
        """模拟AI响应"""
        responses = [
            "我理解您的需求，正在为您处理...",
            "好的，我来帮您完成这个任务。",
            "请稍等，我正在分析您的请求...",
            "收到，正在执行相关操作...",
            "我明白了，让我为您提供帮助。"
        ]
        import random
        response = random.choice(responses)
        self.add_message("AI助手", response)
    
    def show_desktop_state(self):
        """显示桌面状态"""
        try:
            # 获取桌面状态
            desktop_state = self.desktop.get_state(use_vision=False)
            apps = desktop_state.apps_to_string()
            active_app = desktop_state.active_app_to_string()
            
            state_info = f"当前活动应用：{active_app}\n\n已打开的应用：\n{apps}"
            self.add_message("AI助手", f"桌面状态信息：\n{state_info}")
        except Exception as e:
            self.add_message("AI助手", f"获取桌面状态失败：{str(e)}")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
可用功能：
1. 桌面状态 - 查看当前桌面状态
2. 帮助 - 显示此帮助信息
3. 退出 - 退出程序

更多功能正在开发中...
        """
        self.add_message("AI助手", help_text)
    
    def quit_app(self):
        """退出应用"""
        if messagebox.askokcancel("确认", "确定要退出AI助手吗？"):
            self.is_running = False
            if self.chat_window:
                self.chat_window.destroy()
            self.root.quit()
            sys.exit()
    
    def run(self):
        """运行应用"""
        try:
            self.is_running = True
            self.create_floating_button()
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"程序运行出错：{e}")
        finally:
            self.is_running = False

def main():
    """主函数"""
    print("=" * 50)
    print("桌面AI助手启动中...")
    print("=" * 50)
    
    # 检查依赖
    try:
        import tkinter
        import pyautogui
        import pyperclip
    except ImportError as e:
        print(f"缺少必要的依赖包：{e}")
        print("请运行 install.bat 安装依赖")
        input("按回车键退出...")
        return
    
    # 创建并运行助手
    assistant = DesktopAIAssistant()
    assistant.run()

if __name__ == "__main__":
    main()
