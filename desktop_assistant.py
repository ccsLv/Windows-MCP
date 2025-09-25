#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面AI助手 - 基于Windows MCP和Qwen3的悬浮球AI助手
"""

import sys
import os
import json
import asyncio
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Windows MCP相关模块
from src.desktop import Desktop
import uiautomation as ua
import pyautogui as pg
import pyperclip as pc
import requests
from textwrap import dedent

# 导入GUI相关模块
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    from tkinter.font import Font
    import tkinter.simpledialog as simpledialog
except ImportError:
    print("需要安装tkinter: pip install tk")
    sys.exit(1)

# 导入OpenAI客户端用于Qwen3
try:
    from openai import AsyncOpenAI
except ImportError:
    print("需要安装openai: pip install openai")
    sys.exit(1)

# 配置pyautogui
pg.FAILSAFE = False
pg.PAUSE = 0.1

@dataclass
class Config:
    """配置类"""
    api_key: str = "sk-ac3a4329ad1040228a0607564d13ac15"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus"
    window_width: int = 400
    window_height: int = 500
    ball_size: int = 60
    ball_color: str = "#4A90E2"
    ball_hover_color: str = "#357ABD"
    chat_bg_color: str = "#F5F5F5"
    user_bg_color: str = "#4A90E2"
    ai_bg_color: str = "#FFFFFF"
    font_family: str = "Microsoft YaHei UI"
    font_size: int = 10

class Qwen3Client:
    """Qwen3 API客户端"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.conversation_history = []
        
    async def chat(self, message: str, use_tools: bool = True) -> str:
        """与Qwen3对话"""
        try:
            # 添加用户消息到历史
            self.conversation_history.append({"role": "user", "content": message})
            
            # 构建系统提示
            system_prompt = self._build_system_prompt()
            
            # 准备消息
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
            
            # 准备工具定义
            tools = self._get_tools() if use_tools else None
            
            # 调用API
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else None,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 处理响应
            message_response = response.choices[0].message
            
            # 如果有工具调用
            if message_response.tool_calls:
                # 执行工具调用
                tool_results = await self._execute_tools(message_response.tool_calls)
                
                # 添加助手消息和工具结果到历史
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": message_response.content or "",
                    "tool_calls": message_response.tool_calls
                })
                
                # 构建工具结果消息
                tool_messages = []
                for i, tool_call in enumerate(message_response.tool_calls):
                    tool_messages.append({
                        "role": "tool",
                        "content": tool_results[i],
                        "tool_call_id": tool_call.id
                    })
                
                # 添加工具结果到历史
                self.conversation_history.extend(tool_messages)
                
                # 再次调用API获取最终响应
                final_messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
                
                final_response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=final_messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                final_content = final_response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": final_content})
                return final_content
            else:
                # 普通对话
                content = message_response.content
                self.conversation_history.append({"role": "assistant", "content": content})
                return content
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """你是一个智能桌面助手，可以帮助用户操控Windows电脑。你可以：

1. 启动应用程序
2. 执行PowerShell命令
3. 获取桌面状态和UI元素信息
4. 点击、输入、滚动等UI操作
5. 复制粘贴文本
6. 窗口管理（切换、调整大小、移动）
7. 键盘快捷键操作
8. 网页内容抓取

请用中文回复，并且要友好、专业。当用户询问如何操作时，你可以直接使用工具来帮助用户完成任务。"""
    
    def _get_tools(self) -> List[Dict]:
        """获取工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "launch_app",
                    "description": "启动Windows应用程序",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "应用程序名称，如notepad、calculator、chrome等"
                            }
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_powershell",
                    "description": "执行PowerShell命令",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "要执行的PowerShell命令"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_desktop_state",
                    "description": "获取当前桌面状态，包括打开的应用程序和UI元素",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "use_vision": {
                                "type": "boolean",
                                "description": "是否包含屏幕截图"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "click_element",
                    "description": "点击指定坐标的UI元素",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "X坐标"},
                            "y": {"type": "integer", "description": "Y坐标"},
                            "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "鼠标按钮"},
                            "clicks": {"type": "integer", "description": "点击次数"}
                        },
                        "required": ["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description": "在指定位置输入文本",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "X坐标"},
                            "y": {"type": "integer", "description": "Y坐标"},
                            "text": {"type": "string", "description": "要输入的文本"},
                            "clear": {"type": "boolean", "description": "是否清空现有文本"},
                            "press_enter": {"type": "boolean", "description": "输入后是否按回车"}
                        },
                        "required": ["x", "y", "text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scroll_window",
                    "description": "滚动窗口",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "X坐标"},
                            "y": {"type": "integer", "description": "Y坐标"},
                            "direction": {"type": "string", "enum": ["up", "down", "left", "right"], "description": "滚动方向"},
                            "wheel_times": {"type": "integer", "description": "滚动次数"}
                        },
                        "required": ["x", "y", "direction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clipboard_operation",
                    "description": "剪贴板操作",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["copy", "paste"], "description": "操作类型"},
                            "text": {"type": "string", "description": "要复制的文本（仅copy操作需要）"}
                        },
                        "required": ["operation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "window_management",
                    "description": "窗口管理操作",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["switch", "resize", "move"], "description": "操作类型"},
                            "app_name": {"type": "string", "description": "应用程序名称"},
                            "width": {"type": "integer", "description": "窗口宽度"},
                            "height": {"type": "integer", "description": "窗口高度"},
                            "x": {"type": "integer", "description": "X坐标"},
                            "y": {"type": "integer", "description": "Y坐标"}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "keyboard_shortcut",
                    "description": "执行键盘快捷键",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keys": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "按键列表，如['ctrl', 'c']"
                            }
                        },
                        "required": ["keys"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_webpage",
                    "description": "抓取网页内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "网页URL"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    
    async def _execute_tools(self, tool_calls: List[Any]) -> List[str]:
        """执行工具调用"""
        results = []
        desktop = Desktop()
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            try:
                if function_name == "launch_app":
                    result, status = desktop.launch_app(arguments["name"].lower())
                    results.append(f"启动应用: {result}")
                    
                elif function_name == "execute_powershell":
                    result, status_code = desktop.execute_command(arguments["command"])
                    results.append(f"PowerShell输出: {result}\n状态码: {status_code}")
                    
                elif function_name == "get_desktop_state":
                    use_vision = arguments.get("use_vision", False)
                    desktop_state = desktop.get_state(use_vision=use_vision)
                    interactive_elements = desktop_state.tree_state.interactive_elements_to_string()
                    informative_elements = desktop_state.tree_state.informative_elements_to_string()
                    apps = desktop_state.apps_to_string()
                    active_app = desktop_state.active_app_to_string()
                    
                    state_info = f"""当前桌面状态:
活动应用: {active_app}
打开的应用: {apps}
交互元素: {interactive_elements or '无'}
信息元素: {informative_elements or '无'}"""
                    results.append(state_info)
                    
                elif function_name == "click_element":
                    x, y = arguments["x"], arguments["y"]
                    button = arguments.get("button", "left")
                    clicks = arguments.get("clicks", 1)
                    
                    pg.moveTo(x, y)
                    control = desktop.get_element_under_cursor()
                    pg.click(x=x, y=y, button=button, clicks=clicks)
                    results.append(f"点击了 {control.Name} 元素在坐标 ({x}, {y})")
                    
                elif function_name == "type_text":
                    x, y = arguments["x"], arguments["y"]
                    text = arguments["text"]
                    clear = arguments.get("clear", False)
                    press_enter = arguments.get("press_enter", False)
                    
                    pg.click(x=x, y=y)
                    control = desktop.get_element_under_cursor()
                    
                    if clear:
                        pg.hotkey('ctrl', 'a')
                        pg.press('backspace')
                    
                    pg.typewrite(text, interval=0.1)
                    
                    if press_enter:
                        pg.press('enter')
                    
                    results.append(f"在 {control.Name} 元素输入了: {text}")
                    
                elif function_name == "scroll_window":
                    x, y = arguments["x"], arguments["y"]
                    direction = arguments["direction"]
                    wheel_times = arguments.get("wheel_times", 1)
                    
                    pg.moveTo(x, y)
                    
                    if direction == "up":
                        ua.WheelUp(wheel_times)
                    elif direction == "down":
                        ua.WheelDown(wheel_times)
                    elif direction == "left":
                        pg.keyDown('Shift')
                        ua.WheelUp(wheel_times)
                        pg.keyUp('Shift')
                    elif direction == "right":
                        pg.keyDown('Shift')
                        ua.WheelDown(wheel_times)
                        pg.keyUp('Shift')
                    
                    results.append(f"在坐标 ({x}, {y}) 向{direction}滚动了{wheel_times}次")
                    
                elif function_name == "clipboard_operation":
                    operation = arguments["operation"]
                    if operation == "copy":
                        text = arguments["text"]
                        pc.copy(text)
                        results.append(f"已复制到剪贴板: {text}")
                    elif operation == "paste":
                        content = pc.paste()
                        results.append(f"剪贴板内容: {content}")
                        
                elif function_name == "window_management":
                    action = arguments["action"]
                    if action == "switch":
                        app_name = arguments["app_name"]
                        result, status = desktop.switch_app(app_name)
                        results.append(f"切换到应用: {result}")
                    elif action == "resize":
                        width = arguments.get("width")
                        height = arguments.get("height")
                        x = arguments.get("x")
                        y = arguments.get("y")
                        size_tuple = (width, height) if width and height else None
                        loc_tuple = (x, y) if x and y else None
                        result, _ = desktop.resize_app(size_tuple, loc_tuple)
                        results.append(f"窗口管理: {result}")
                        
                elif function_name == "keyboard_shortcut":
                    keys = arguments["keys"]
                    pg.hotkey(*keys)
                    results.append(f"执行快捷键: {'+'.join(keys)}")
                    
                elif function_name == "scrape_webpage":
                    url = arguments["url"]
                    response = requests.get(url, timeout=10)
                    from markdownify import markdownify
                    content = markdownify(html=response.text)
                    results.append(f"网页内容:\n{content[:500]}...")
                    
                else:
                    results.append(f"未知工具: {function_name}")
                    
            except Exception as e:
                results.append(f"执行工具 {function_name} 时出错: {str(e)}")
        
        return results

class FloatingBall:
    """悬浮球类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.root = None
        self.chat_window = None
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.qwen_client = Qwen3Client(config)
        
    def create_floating_ball(self):
        """创建悬浮球"""
        self.root = tk.Tk()
        self.root.title("AI助手")
        self.root.overrideredirect(True)  # 无边框窗口
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-alpha', 0.9)  # 半透明
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置初始位置（右下角）
        x = screen_width - self.config.ball_size - 20
        y = screen_height - self.config.ball_size - 100
        
        self.root.geometry(f"{self.config.ball_size}x{self.config.ball_size}+{x}+{y}")
        
        # 创建悬浮球
        self.ball_frame = tk.Frame(
            self.root,
            width=self.config.ball_size,
            height=self.config.ball_size,
            bg=self.config.ball_color,
            relief="raised",
            bd=2
        )
        self.ball_frame.pack(fill="both", expand=True)
        
        # 添加AI图标或文字
        self.ball_label = tk.Label(
            self.ball_frame,
            text="AI",
            font=(self.config.font_family, 16, "bold"),
            fg="white",
            bg=self.config.ball_color
        )
        self.ball_label.pack(expand=True)
        
        # 绑定事件
        self.ball_frame.bind("<Button-1>", self.start_drag)
        self.ball_frame.bind("<B1-Motion>", self.drag)
        self.ball_frame.bind("<ButtonRelease-1>", self.stop_drag)
        self.ball_frame.bind("<Double-Button-1>", self.toggle_chat)
        self.ball_label.bind("<Button-1>", self.start_drag)
        self.ball_label.bind("<B1-Motion>", self.drag)
        self.ball_label.bind("<ButtonRelease-1>", self.stop_drag)
        self.ball_label.bind("<Double-Button-1>", self.toggle_chat)
        
        # 鼠标悬停效果
        self.ball_frame.bind("<Enter>", self.on_enter)
        self.ball_frame.bind("<Leave>", self.on_leave)
        
    def start_drag(self, event):
        """开始拖拽"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
    def drag(self, event):
        """拖拽中"""
        if self.is_dragging:
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
            
    def stop_drag(self, event):
        """停止拖拽"""
        self.is_dragging = False
        
    def on_enter(self, event):
        """鼠标进入"""
        self.ball_frame.config(bg=self.config.ball_hover_color)
        self.ball_label.config(bg=self.config.ball_hover_color)
        
    def on_leave(self, event):
        """鼠标离开"""
        self.ball_frame.config(bg=self.config.ball_color)
        self.ball_label.config(bg=self.config.ball_color)
        
    def toggle_chat(self, event):
        """切换聊天窗口"""
        if self.chat_window is None or not self.chat_window.winfo_exists():
            self.create_chat_window()
        else:
            self.chat_window.destroy()
            self.chat_window = None
            
    def create_chat_window(self):
        """创建聊天窗口"""
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("AI助手对话")
        self.chat_window.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.chat_window.attributes('-topmost', True)
        
        # 设置窗口位置（在悬浮球旁边）
        ball_x = self.root.winfo_x()
        ball_y = self.root.winfo_y()
        chat_x = ball_x - self.config.window_width - 10
        chat_y = ball_y
        
        # 确保窗口不超出屏幕
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if chat_x < 0:
            chat_x = ball_x + self.config.ball_size + 10
        if chat_y + self.config.window_height > screen_height:
            chat_y = screen_height - self.config.window_height - 50
            
        self.chat_window.geometry(f"{self.config.window_width}x{self.config.window_height}+{chat_x}+{chat_y}")
        
        # 创建聊天界面
        self.create_chat_interface()
        
    def create_chat_interface(self):
        """创建聊天界面"""
        # 主框架
        main_frame = tk.Frame(self.chat_window, bg=self.config.chat_bg_color)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=(self.config.font_family, self.config.font_size),
            bg="white",
            state="disabled",
            height=20
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 10))
        
        # 输入框架
        input_frame = tk.Frame(main_frame, bg=self.config.chat_bg_color)
        input_frame.pack(fill="x", pady=(0, 5))
        
        # 输入框
        self.input_entry = tk.Entry(
            input_frame,
            font=(self.config.font_family, self.config.font_size),
            relief="solid",
            bd=1
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self.send_message)
        
        # 发送按钮
        send_button = tk.Button(
            input_frame,
            text="发送",
            command=self.send_message,
            font=(self.config.font_family, self.config.font_size),
            bg=self.config.user_bg_color,
            fg="white",
            relief="flat",
            padx=10
        )
        send_button.pack(side="right")
        
        # 清空按钮
        clear_button = tk.Button(
            main_frame,
            text="清空对话",
            command=self.clear_chat,
            font=(self.config.font_family, self.config.font_size - 1),
            bg="#FF6B6B",
            fg="white",
            relief="flat",
            padx=5
        )
        clear_button.pack(pady=(0, 5))
        
        # 聚焦到输入框
        self.input_entry.focus()
        
    def add_message(self, message: str, is_user: bool = True):
        """添加消息到聊天显示区域"""
        self.chat_display.config(state="normal")
        
        # 设置消息样式
        if is_user:
            prefix = "用户: "
            bg_color = self.config.user_bg_color
            fg_color = "white"
        else:
            prefix = "AI助手: "
            bg_color = self.config.ai_bg_color
            fg_color = "black"
            
        # 添加消息
        self.chat_display.insert(tk.END, prefix, "user_tag" if is_user else "ai_tag")
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # 配置标签样式
        self.chat_display.tag_config("user_tag", foreground=fg_color, background=bg_color)
        self.chat_display.tag_config("ai_tag", foreground=fg_color, background=bg_color)
        
        # 滚动到底部
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")
        
    def send_message(self, event=None):
        """发送消息"""
        message = self.input_entry.get().strip()
        if not message:
            return
            
        # 清空输入框
        self.input_entry.delete(0, tk.END)
        
        # 显示用户消息
        self.add_message(message, is_user=True)
        
        # 显示"正在思考..."
        self.add_message("正在思考...", is_user=False)
        
        # 异步获取AI响应
        threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()
        
    def get_ai_response(self, message: str):
        """获取AI响应"""
        try:
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(self.qwen_client.chat(message))
            loop.close()
            
            # 在主线程中更新UI
            self.root.after(0, self.update_ai_response, response)
            
        except Exception as e:
            error_msg = f"获取AI响应时出错: {str(e)}"
            self.root.after(0, self.update_ai_response, error_msg)
            
    def update_ai_response(self, response: str):
        """更新AI响应"""
        # 删除"正在思考..."消息
        self.chat_display.config(state="normal")
        self.chat_display.delete("end-2l", "end-1l")  # 删除最后一行
        self.chat_display.config(state="disabled")
        
        # 添加AI响应
        self.add_message(response, is_user=False)
        
    def clear_chat(self):
        """清空聊天记录"""
        self.chat_display.config(state="normal")
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state="disabled")
        
        # 清空对话历史
        self.qwen_client.conversation_history = []
        
    def run(self):
        """运行悬浮球"""
        self.create_floating_ball()
        self.root.mainloop()

def main():
    """主函数"""
    print("启动桌面AI助手...")
    
    # 创建配置
    config = Config()
    
    # 创建并运行悬浮球
    ball = FloatingBall(config)
    
    try:
        ball.run()
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"运行出错: {e}")
        messagebox.showerror("错误", f"运行出错: {e}")

if __name__ == "__main__":
    main()
