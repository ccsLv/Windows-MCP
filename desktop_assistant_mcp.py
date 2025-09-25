#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面AI助手 - 基于Windows MCP和Qwen3的悬浮球AI助手（MCP客户端版本）
"""

import sys
import os
import json
import asyncio
import threading
import time
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入MCP客户端
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("需要安装mcp: pip install mcp")
    sys.exit(1)

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

class MCPClient:
    """MCP客户端，用于与Windows MCP服务器通信"""
    
    def __init__(self):
        self.session = None
        self.server_process = None
        
    async def connect(self):
        """连接到Windows MCP服务器"""
        try:
            # 启动MCP服务器进程
            server_params = StdioServerParameters(
                command="python",
                args=[os.path.join(os.path.dirname(__file__), "main.py")]
            )
            
            # 创建stdio客户端
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    
                    # 初始化会话
                    await session.initialize()
                    
                    # 获取可用工具
                    tools = await session.list_tools()
                    print(f"连接到MCP服务器成功，可用工具: {[tool.name for tool in tools.tools]}")
                    
                    return True
                    
        except Exception as e:
            print(f"连接MCP服务器失败: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用MCP工具"""
        if not self.session:
            return "错误: 未连接到MCP服务器"
            
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "工具执行完成"
        except Exception as e:
            return f"调用工具 {tool_name} 失败: {str(e)}"

class Qwen3Client:
    """Qwen3 API客户端"""
    
    def __init__(self, config: Config, mcp_client: MCPClient):
        self.config = config
        self.mcp_client = mcp_client
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
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            try:
                # 映射工具名称到MCP工具名称
                mcp_tool_mapping = {
                    "launch_app": "Launch-Tool",
                    "execute_powershell": "Powershell-Tool",
                    "get_desktop_state": "State-Tool",
                    "click_element": "Click-Tool",
                    "type_text": "Type-Tool",
                    "scroll_window": "Scroll-Tool",
                    "clipboard_operation": "Clipboard-Tool",
                    "window_management": "Switch-Tool",  # 简化处理
                    "keyboard_shortcut": "Shortcut-Tool",
                    "scrape_webpage": "Scrape-Tool"
                }
                
                mcp_tool_name = mcp_tool_mapping.get(function_name)
                if not mcp_tool_name:
                    results.append(f"未知工具: {function_name}")
                    continue
                
                # 转换参数格式
                mcp_arguments = self._convert_arguments(function_name, arguments)
                
                # 调用MCP工具
                result = await self.mcp_client.call_tool(mcp_tool_name, mcp_arguments)
                results.append(result)
                
            except Exception as e:
                results.append(f"执行工具 {function_name} 时出错: {str(e)}")
        
        return results
    
    def _convert_arguments(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """转换参数格式以匹配MCP工具"""
        if function_name == "launch_app":
            return {"name": arguments["name"]}
        elif function_name == "execute_powershell":
            return {"command": arguments["command"]}
        elif function_name == "get_desktop_state":
            return {"use_vision": arguments.get("use_vision", False)}
        elif function_name == "click_element":
            return {
                "loc": [arguments["x"], arguments["y"]],
                "button": arguments.get("button", "left"),
                "clicks": arguments.get("clicks", 1)
            }
        elif function_name == "type_text":
            return {
                "loc": [arguments["x"], arguments["y"]],
                "text": arguments["text"],
                "clear": arguments.get("clear", False),
                "press_enter": arguments.get("press_enter", False)
            }
        elif function_name == "scroll_window":
            return {
                "loc": [arguments["x"], arguments["y"]],
                "direction": arguments["direction"],
                "wheel_times": arguments.get("wheel_times", 1)
            }
        elif function_name == "clipboard_operation":
            return {
                "mode": arguments["operation"],
                "text": arguments.get("text")
            }
        elif function_name == "window_management":
            if arguments["action"] == "switch":
                return {"name": arguments["app_name"]}
            elif arguments["action"] == "resize":
                return {
                    "size": [arguments.get("width", 800), arguments.get("height", 600)],
                    "loc": [arguments.get("x", 100), arguments.get("y", 100)]
                }
        elif function_name == "keyboard_shortcut":
            return {"shortcut": arguments["keys"]}
        elif function_name == "scrape_webpage":
            return {"url": arguments["url"]}
        
        return arguments

class FloatingBall:
    """悬浮球类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.root = None
        self.chat_window = None
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.mcp_client = MCPClient()
        self.qwen_client = None
        
    async def initialize(self):
        """初始化MCP客户端和Qwen客户端"""
        # 连接MCP服务器
        if await self.mcp_client.connect():
            self.qwen_client = Qwen3Client(self.config, self.mcp_client)
            return True
        return False
        
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
        if self.qwen_client:
            self.qwen_client.conversation_history = []
        
    def run(self):
        """运行悬浮球"""
        self.create_floating_ball()
        self.root.mainloop()

async def main():
    """主函数"""
    print("启动桌面AI助手（MCP版本）...")
    
    # 创建配置
    config = Config()
    
    # 创建悬浮球
    ball = FloatingBall(config)
    
    # 初始化MCP连接
    if not await ball.initialize():
        print("初始化MCP连接失败")
        return
    
    print("MCP连接初始化成功")
    
    # 运行悬浮球
    try:
        ball.run()
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"运行出错: {e}")
        messagebox.showerror("错误", f"运行出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())
