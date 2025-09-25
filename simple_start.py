#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版桌面AI助手启动脚本
"""

import sys
import os
import asyncio
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Windows MCP相关模块
from src.desktop import Desktop
import uiautomation as ua
import pyautogui as pg
import pyperclip as pc
import requests
from textwrap import dedent
import json
import subprocess
import time

# 导入GUI相关模块
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    from tkinter.font import Font
except ImportError:
    print("错误: 需要安装tkinter模块")
    input("按回车键退出...")
    sys.exit(1)

# 导入OpenAI客户端用于Qwen3
try:
    from openai import AsyncOpenAI
except ImportError:
    print("错误: 需要安装openai模块")
    print("请运行: pip install openai")
    input("按回车键退出...")
    sys.exit(1)

# 配置pyautogui
pg.FAILSAFE = False
pg.PAUSE = 0.1

@dataclass
class SimpleConfig:
    """简化配置类"""
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

class SimpleQwenClient:
    """简化版Qwen3客户端"""
    
    def __init__(self, config: SimpleConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.conversation_history = []
        # 初始化桌面操作对象（已包含COM初始化）
        self.desktop = Desktop()
        
    async def chat(self, message: str) -> str:
        """与Qwen3对话"""
        try:
            # 添加用户消息到历史
            self.conversation_history.append({"role": "user", "content": message})
            
            # 构建系统提示 - 自主决策版本：AI主动思考并执行
            system_prompt = """你是一个智能桌面助手，具备自主决策能力。你的核心任务是理解用户需求并主动完成，遇到问题时自动寻找解决方案。

🎯 核心原则：
1. 理解用户真实意图，制定完整执行计划
2. 遇到问题时自动尝试多种解决方案
3. 持续工作直到任务完成，绝不中途停止
4. 主动思考替代方案，如Chrome启动失败则尝试Edge
5. 实时反馈执行进度和遇到的问题

🛠️ 可用工具：
1. launch_app - 启动应用程序（内置6种启动方法自动重试）
2. wechat_operation - 微信操作（启动微信、搜索联系人、发送消息等）
3. execute_command - 执行PowerShell命令
4. get_desktop_state - 获取桌面状态
5. click_element - 点击UI元素
6. type_text - 输入文本
7. scroll_window - 滚动窗口
8. clipboard_operation - 剪贴板操作
9. window_management - 窗口管理
10. keyboard_shortcut - 键盘快捷键
11. scrape_webpage - 网页抓取
12. write_file_content - 写入文件内容

🚀 执行策略：
- 用户说"打开Chrome并搜索天气" → 先启动Chrome，失败则尝试Edge，再失败则尝试其他浏览器
- 启动成功后自动搜索天气，失败则尝试其他搜索方式
- 用户说"创建文档并写入内容" → 先创建文档，然后立即写入指定内容
- 每个步骤都要尝试多种方法，直到成功或所有方法都失败
- 实时报告执行进度："正在启动Chrome..." → "Chrome启动失败，尝试Edge..." → "Edge启动成功，正在搜索天气..."

💡 智能思考：
- 分析任务复杂度，制定分步执行计划
- 预判可能遇到的问题，准备备用方案
- 根据执行结果调整策略
- 主动寻找替代解决方案
- 特别注意复合任务：创建+写入、启动+操作、搜索+点击等

⚠️ 重要提醒：
- 你是完全自主的AI助手，遇到任何问题都要主动解决
- 不要停下来等用户确认，要持续工作直到任务完成
- 如果某个方法失败，立即尝试其他方法
- 始终保持积极态度，主动寻找解决方案
- 实时反馈你的思考和执行过程
- 对于"创建文档并写入内容"这样的复合任务，必须完成所有步骤

🚨 复合任务处理规则：
- "创建文档并写入内容" = 创建文档 + 写入内容（两个步骤都必须完成）
- "打开应用并搜索" = 打开应用 + 执行搜索（两个步骤都必须完成）
- "启动程序并点击按钮" = 启动程序 + 点击按钮（两个步骤都必须完成）
- 绝对不要只完成第一个步骤就停止！

记住：你是完全自主工作的AI助手，遇到问题要主动解决，复合任务要完整完成，不要停下来等用户确认！"""
            
            # 准备消息
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
            
            # 准备工具定义
            tools = self._get_tools()
            
            # 调用API
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools,
                tool_choice="required",  # 强制使用工具
                temperature=0.7,
                max_tokens=2000
            )
            
            # 处理响应
            message_response = response.choices[0].message
            
            # 如果有工具调用
            if message_response.tool_calls:
                # 执行工具调用
                tool_results = await self._execute_tools(message_response.tool_calls)
                
                # 添加助手消息到历史（包含tool_calls）
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
            import traceback
            error_details = traceback.format_exc()
            # 增强错误处理，提供更友好的错误信息
            error_msg = f"❌ 遇到错误: {str(e)}"
            if "tool_calls" in str(e).lower():
                error_msg += "\n🔄 正在尝试重新处理工具调用..."
            elif "connection" in str(e).lower():
                error_msg += "\n🌐 网络连接问题，请检查网络设置"
            elif "api" in str(e).lower():
                error_msg += "\n🔑 API调用失败，请检查API密钥和网络连接"
            else:
                error_msg += f"\n📋 详细错误信息:\n{error_details}"
            return error_msg
    
    async def chat_stream(self, message: str, ui_callback) -> str:
        """流式聊天 - 实时显示AI思考和执行过程，支持自主连续工作"""
        try:
            # 添加用户消息到历史
            self.conversation_history.append({"role": "user", "content": message})
            
            # 构建系统提示 - 自主决策版本：AI主动思考并执行
            system_prompt = """你是一个智能桌面助手，具备完全自主决策能力。你的核心任务是理解用户需求并主动完成整个任务流程，遇到问题时自动寻找解决方案。

🎯 核心原则：
1. 理解用户真实意图，制定完整执行计划
2. 遇到问题时自动尝试多种解决方案
3. 持续工作直到任务完成，绝不中途停止
4. 主动思考替代方案，如Chrome启动失败则尝试Edge
5. 实时反馈执行进度和遇到的问题
6. 完全自主工作，不需要用户确认或输入"继续"

🛠️ 可用工具：
1. launch_app - 启动应用程序（内置6种启动方法自动重试）
2. wechat_operation - 微信操作（启动微信、搜索联系人、发送消息等）
3. execute_command - 执行PowerShell命令
4. get_desktop_state - 获取桌面状态
5. click_element - 点击UI元素
6. type_text - 输入文本
7. scroll_window - 滚动窗口
8. clipboard_operation - 剪贴板操作
9. window_management - 窗口管理
10. keyboard_shortcut - 键盘快捷键
11. scrape_webpage - 网页抓取
12. write_file_content - 写入文件内容

🚀 执行策略：
- 用户说"打开Chrome并搜索天气" → 先启动Chrome，失败则尝试Edge，再失败则尝试其他浏览器
- 启动成功后自动搜索天气，失败则尝试其他搜索方式
- 用户说"创建文档并写入内容" → 先创建文档，然后立即写入指定内容
- 用户说"打开微信，找到方志豪，给他发一个信息：白老师，你过来一下" → 使用wechat_operation工具依次执行：启动微信、搜索联系人、发送消息
- 每个步骤都要尝试多种方法，直到成功或所有方法都失败
- 实时报告执行进度："正在启动Chrome..." → "Chrome启动失败，尝试Edge..." → "Edge启动成功，正在搜索天气..."
- 完成一个步骤后立即继续下一步，不要等待用户确认

💡 智能思考：
- 分析任务复杂度，制定分步执行计划
- 预判可能遇到的问题，准备备用方案
- 根据执行结果调整策略
- 主动寻找替代解决方案
- 如果任务需要多个步骤，自动规划并执行所有步骤
- 特别注意复合任务：创建+写入、启动+操作、搜索+点击等

⚠️ 重要提醒：
- 你是完全自主的AI助手，遇到任何问题都要主动解决
- 不要停下来等用户确认，要持续工作直到任务完成
- 如果某个方法失败，立即尝试其他方法
- 始终保持积极态度，主动寻找解决方案
- 实时反馈你的思考和执行过程
- 完成任务后给出总结，不要等待用户输入
- 当你说"让我尝试另一种方法"时，必须立即执行相应的工具调用
- 绝对不要只是描述要做什么，而要直接执行工具调用
- 对于"创建文档并写入内容"这样的复合任务，必须完成所有步骤

🚨 复合任务处理规则：
- "创建文档并写入内容" = 创建文档 + 写入内容（两个步骤都必须完成）
- "打开应用并搜索" = 打开应用 + 执行搜索（两个步骤都必须完成）
- "启动程序并点击按钮" = 启动程序 + 点击按钮（两个步骤都必须完成）
- 绝对不要只完成第一个步骤就停止！

🚨 关键行为准则：
- 遇到问题时，立即使用工具调用解决问题，不要停下来等待
- 当提到"让我尝试"、"我可以"、"我将"时，必须立即执行工具调用
- 不要只是告诉用户你要做什么，而是直接去做
- 每个"让我..."后面都必须跟一个工具调用
- 对于"打开QQ"这样的请求，必须使用launch_app工具，不要提供手动操作指导
- 绝对不要说"我无法直接帮你"，而要使用工具直接操作

🛠️ 工具使用强制要求：
- 用户说"打开QQ" → 必须调用launch_app工具
- 用户说"启动Chrome" → 必须调用launch_app工具  
- 用户说"执行命令" → 必须调用execute_command工具
- 用户说"获取桌面状态" → 必须调用get_desktop_state工具
- 用户说"创建文档并写入内容" → 必须调用execute_command创建文档 + write_file_content写入内容
- 绝对不要提供手动操作指导，而要直接使用工具执行
- 绝对不要只是描述要做什么，而要直接执行工具调用
- 对于任何操作请求，都必须使用相应的工具，不能只回复文本

记住：你是完全自主工作的AI助手，遇到问题要主动解决，复合任务要完整完成，绝不停下来等用户确认！"""
            
            # 开始自主工作循环
            await self._autonomous_work_loop(message, ui_callback, system_prompt)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            
            # 增强错误处理，提供更友好的错误信息
            error_msg = f"❌ 遇到错误: {str(e)}"
            if "tool_calls" in str(e).lower():
                error_msg += "\n🔄 正在尝试重新处理工具调用..."
                ui_callback.root.after(0, ui_callback.add_streaming_message, error_msg, False)
                # 尝试重新处理
                ui_callback.root.after(1000, lambda: self._retry_tool_calls(message, ui_callback))
            elif "connection" in str(e).lower():
                error_msg += "\n🌐 网络连接问题，请检查网络设置"
                ui_callback.root.after(0, ui_callback.add_streaming_message, error_msg, False)
            elif "api" in str(e).lower():
                error_msg += "\n🔑 API调用失败，请检查API密钥和网络连接"
                ui_callback.root.after(0, ui_callback.add_streaming_message, error_msg, False)
            else:
                error_msg += f"\n📋 详细错误信息:\n{error_details}"
                ui_callback.root.after(0, ui_callback.add_streaming_message, error_msg, False)
            
            ui_callback.root.after(0, ui_callback.stop_working_animation)
    
    async def _autonomous_work_loop(self, message: str, ui_callback, system_prompt: str, max_iterations: int = 10):
        """自主工作循环 - 持续执行直到任务完成"""
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # 显示当前迭代状态
            ui_callback.root.after(0, ui_callback.update_status, f"正在执行第{iteration}步...")
            
            # 准备消息
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
            
            # 准备工具定义
            tools = self._get_tools()
            
            # 显示思考状态
            if iteration == 1:
                ui_callback.root.after(0, ui_callback.add_streaming_message, "🤔 正在分析您的需求...", False)
            else:
                ui_callback.root.after(0, ui_callback.add_streaming_message, f"🔄 继续执行第{iteration}步...", False)
            
            # 调用API
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools,
                tool_choice="required",  # 强制使用工具
                temperature=0.7,
                max_tokens=2000
            )
            
            # 处理响应
            message_response = response.choices[0].message
            
            # 如果有工具调用
            if message_response.tool_calls:
                # 添加助手消息到历史（包含tool_calls）
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": message_response.content or "",
                    "tool_calls": message_response.tool_calls
                })
                
                # 执行工具调用并流式显示结果
                tool_results = await self._execute_tools_stream(message_response.tool_calls, ui_callback)
                
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
                
                # 检查是否还需要继续工作
                if self._should_continue_working(tool_results, message):
                    ui_callback.root.after(0, ui_callback.add_streaming_message, "🔄 继续执行下一步...", False)
                    continue
                else:
                    # 任务完成，生成最终总结
                    ui_callback.root.after(0, ui_callback.update_status, "正在生成最终总结...")
                    
                    final_messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
                    
                    final_response = await self.client.chat.completions.create(
                        model=self.config.model,
                        messages=final_messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    final_content = final_response.choices[0].message.content
                    self.conversation_history.append({"role": "assistant", "content": final_content})
                    
                    # 流式显示最终总结
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ 任务完成！\n\n{final_content}", False)
                    break
            else:
                # 普通对话，任务完成
                content = message_response.content
                self.conversation_history.append({"role": "assistant", "content": content})
                ui_callback.root.after(0, ui_callback.add_streaming_message, content, False)
                break
        
        # 如果达到最大迭代次数
        if iteration >= max_iterations:
            ui_callback.root.after(0, ui_callback.add_streaming_message, "⚠️ 已达到最大执行次数，任务可能未完全完成。", False)
        
        # 停止工作动画
        ui_callback.root.after(0, ui_callback.stop_working_animation)
    
    def _should_continue_working(self, tool_results: List[str], original_message: str) -> bool:
        """判断是否应该继续工作 - 智能决策机制"""
        
        # 1. 检查工具执行结果中的错误信息
        has_errors = False
        has_success = False
        
        for result in tool_results:
            result_lower = result.lower()
            
            # 检查错误关键词
            error_keywords = ["失败", "错误", "无法", "不能", "error", "failed", "exception", "异常", "❌"]
            if any(keyword in result_lower for keyword in error_keywords):
                has_errors = True
            
            # 检查成功关键词
            success_keywords = ["成功", "完成", "启动", "success", "completed", "✅", "已启动", "已打开"]
            if any(keyword in result_lower for keyword in success_keywords):
                has_success = True
        
        # 2. 如果有错误，通常需要重试或尝试其他方法
        if has_errors and not has_success:
            return True
        
        # 3. 检查原始消息是否包含复合任务指示词
        compound_task_keywords = [
            "并", "然后", "接着", "再", "之后", "接下来", "同时", "写入", "写入内容", "写入介绍",
            "and", "then", "next", "after", "also", "同时", "write", "create and write"
        ]
        has_compound_tasks = any(keyword in original_message.lower() for keyword in compound_task_keywords)
        
        # 特别检查文档创建任务
        document_creation_patterns = [
            "创建.*文档.*写入", "创建.*文件.*写入", "创建.*并写入", 
            "create.*document.*write", "create.*file.*write"
        ]
        import re
        has_document_task = any(re.search(pattern, original_message.lower()) for pattern in document_creation_patterns)
        
        # 4. 检查对话历史中是否有未完成的任务指示
        last_assistant_message = None
        if len(self.conversation_history) > 0:
            for msg in reversed(self.conversation_history):
                if msg.get("role") == "assistant" and "content" in msg:
                    last_assistant_message = msg["content"]
                    break
        
        # 5. 检查最后一条助手消息是否包含继续工作的指示
        continue_keywords = [
            "继续", "下一步", "然后", "接着", "continue", "next", "接下来",
            "现在", "接下来", "然后", "接着", "继续执行", "继续工作",
            "让我尝试", "我可以", "我将", "让我", "尝试", "方法", "另一种",
            "技术限制", "遇到问题", "让我先", "让我检查", "让我确认"
        ]
        needs_continuation = False
        if last_assistant_message:
            needs_continuation = any(keyword in last_assistant_message.lower() for keyword in continue_keywords)
        
        # 6. 检查是否启动了应用程序但还没有完成后续操作
        app_launched_but_incomplete = False
        if has_success and any(keyword in str(tool_results).lower() for keyword in ["启动", "launch", "打开", "open"]):
            # 如果启动了应用，检查原始任务是否包含后续操作
            if any(keyword in original_message.lower() for keyword in ["搜索", "输入", "点击", "打开", "search", "type", "click"]):
                app_launched_but_incomplete = True
        
        # 8. 检查是否只完成了创建文档但没有写入内容
        document_created_but_content_missing = False
        if has_success and any(keyword in str(tool_results).lower() for keyword in ["创建", "create", "new-item"]):
            # 如果创建了文档，检查是否还有写入操作
            if has_document_task or "写入" in original_message or "write" in original_message.lower():
                # 检查是否执行了写入操作
                if not any(keyword in str(tool_results).lower() for keyword in ["写入", "write", "write_file_content"]):
                    document_created_but_content_missing = True
        
        # 9. 综合判断
        should_continue = (
            has_errors or  # 有错误需要重试
            (has_success and has_compound_tasks) or  # 有成功且有复合任务
            needs_continuation or  # 明确需要继续
            app_launched_but_incomplete or  # 启动了应用但任务未完成
            document_created_but_content_missing or  # 创建了文档但内容未写入
            has_document_task  # 有文档创建任务需要完成
        )
        
        return should_continue
    
    def _retry_tool_calls(self, message: str, ui_callback):
        """重试工具调用"""
        try:
            ui_callback.root.after(0, ui_callback.add_streaming_message, "🔄 正在重试...", False)
            # 重新开始工作动画
            ui_callback.root.after(0, ui_callback.start_working_animation, "正在重试...")
            # 重新执行聊天
            threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()
        except Exception as e:
            ui_callback.root.after(0, ui_callback.add_streaming_message, f"❌ 重试失败: {str(e)}", False)
            ui_callback.root.after(0, ui_callback.stop_working_animation)
    
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
                    "name": "wechat_operation",
                    "description": "微信操作，包括启动微信、搜索联系人、发送消息等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["launch", "search_contact", "send_message", "get_contacts"],
                                "description": "操作类型：launch-启动微信，search_contact-搜索联系人，send_message-发送消息，get_contacts-获取联系人列表"
                            },
                            "contact_name": {
                                "type": "string",
                                "description": "联系人姓名（搜索和发送消息时需要）"
                            },
                            "message": {
                                "type": "string",
                                "description": "要发送的消息内容（发送消息时需要）"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file_content",
                    "description": "向文件写入内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "content": {"type": "string", "description": "要写入的内容"},
                            "encoding": {"type": "string", "description": "文件编码，默认为utf-8"}
                        },
                        "required": ["file_path", "content"]
                    }
                }
            }
        ]
    
    def _smart_launch_app(self, app_name: str) -> str:
        """智能启动应用，自动尝试多种方法"""
        
        # 记录尝试的方法
        attempts = []
        
        # 方法1: 使用Desktop类的原始方法
        try:
            result, status = self.desktop.launch_app(app_name)
            if status == 0:
                return f"✅ 成功启动 {app_name.title()}: {result}"
            else:
                attempts.append(f"方法1(开始菜单)失败: {result}")
        except Exception as e:
            attempts.append(f"方法1(开始菜单)异常: {str(e)}")
        
        # 方法2: 使用PowerShell的Start-Process直接启动
        try:
            ps_result, ps_status = self.desktop.execute_command(f"Start-Process '{app_name}'")
            if ps_status == 0:
                return f"✅ 通过PowerShell成功启动 {app_name.title()}"
            else:
                attempts.append(f"方法2(PowerShell)失败: {ps_result}")
        except Exception as e:
            attempts.append(f"方法2(PowerShell)异常: {str(e)}")
        
        # 方法3: 尝试常见的应用名称映射
        app_mappings = {
            "notepad": ["notepad.exe", "notepad"],
            "calculator": ["calc.exe", "calculator.exe"], 
            "paint": ["mspaint.exe", "paint.exe"],
            "cmd": ["cmd.exe"],
            "powershell": ["powershell.exe"],
            "explorer": ["explorer.exe"],
            "chrome": ["chrome.exe", "google chrome"],
            "firefox": ["firefox.exe"],
            "edge": ["msedge.exe", "microsoft edge"],
            "vscode": ["code.exe", "visual studio code"],
            "word": ["winword.exe", "microsoft word"],
            "excel": ["excel.exe", "microsoft excel"],
            "task": ["taskmgr.exe", "task manager"],
            "控制面板": ["control.exe", "control panel"],
            "记事本": ["notepad.exe"],
            "计算器": ["calc.exe"],
            "画图": ["mspaint.exe"],
            "qq": ["qq.exe", "qq", "tencent qq", "腾讯qq"],
            "微信": ["wechat.exe", "wechat", "微信"],
            "钉钉": ["dingtalk.exe", "dingtalk", "钉钉"],
            "网易云音乐": ["cloudmusic.exe", "cloudmusic", "网易云音乐"],
            "爱奇艺": ["iqiyi.exe", "iqiyi", "爱奇艺"],
            "优酷": ["youku.exe", "youku", "优酷"],
            "腾讯视频": ["qqlive.exe", "qqlive", "腾讯视频"]
        }
        
        # 获取可能的应用名称
        possible_names = app_mappings.get(app_name, [app_name])
        if app_name not in possible_names:
            possible_names.append(app_name)
        
        for name in possible_names:
            try:
                # 尝试直接使用exe名称
                ps_result, ps_status = self.desktop.execute_command(f"Start-Process '{name}' -ErrorAction SilentlyContinue")
                if ps_status == 0:
                    return f"✅ 通过映射名称 '{name}' 成功启动应用"
                else:
                    attempts.append(f"方法3(映射名称{name})失败")
            except Exception as e:
                attempts.append(f"方法3(映射名称{name})异常: {str(e)}")
        
        # 方法4: 尝试使用cmd启动
        try:
            cmd_result, cmd_status = self.desktop.execute_command(f"cmd /c start {app_name}")
            if cmd_status == 0:
                return f"✅ 通过CMD成功启动 {app_name.title()}"
            else:
                attempts.append(f"方法4(CMD)失败: {cmd_result}")
        except Exception as e:
            attempts.append(f"方法4(CMD)异常: {str(e)}")
        
        # 方法5: 尝试从常见路径启动
        common_paths = [
            f"C:\\Windows\\System32\\{app_name}.exe",
            f"C:\\Windows\\System32\\{app_name}",
            f"C:\\Program Files\\{app_name}\\{app_name}.exe",
            f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe"
        ]
        
        for path in common_paths:
            try:
                path_result, path_status = self.desktop.execute_command(f"if (Test-Path '{path}') {{ Start-Process '{path}'; 'success' }} else {{ 'not found' }}")
                if "success" in path_result:
                    return f"✅ 通过路径 '{path}' 成功启动应用"
                else:
                    attempts.append(f"方法5(路径{path})：文件不存在")
            except Exception as e:
                attempts.append(f"方法5(路径{path})异常: {str(e)}")
        
        # 方法6: 尝试搜索可执行文件
        try:
            search_result, search_status = self.desktop.execute_command(
                f"Get-ChildItem -Path 'C:\\Windows\\System32', 'C:\\Program Files', 'C:\\Program Files (x86)' "
                f"-Name '*{app_name}*.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1"
            )
            if search_status == 0 and search_result.strip():
                found_path = search_result.strip()
                try:
                    exec_result, exec_status = self.desktop.execute_command(f"Start-Process '{found_path}'")
                    if exec_status == 0:
                        return f"✅ 通过搜索找到并启动: {found_path}"
                    else:
                        attempts.append(f"方法6(搜索)找到文件但启动失败: {found_path}")
                except Exception as e:
                    attempts.append(f"方法6(搜索)执行异常: {str(e)}")
            else:
                attempts.append(f"方法6(搜索)未找到匹配文件")
        except Exception as e:
            attempts.append(f"方法6(搜索)异常: {str(e)}")
        
        # 所有方法都失败了
        attempts_summary = "\n".join([f"  - {attempt}" for attempt in attempts])
        return f"❌ 无法启动应用 '{app_name}'\n\n尝试的方法：\n{attempts_summary}\n\n建议：请检查应用名称是否正确，或者应用是否已安装。"
    
    def _wechat_operation(self, action: str, contact_name: str = None, message: str = None) -> str:
        """微信操作的具体实现"""
        try:
            if action == "launch":
                return self._launch_wechat()
            elif action == "search_contact":
                if not contact_name:
                    return "❌ 搜索联系人需要提供联系人姓名"
                return self._search_wechat_contact(contact_name)
            elif action == "send_message":
                if not contact_name or not message:
                    return "❌ 发送消息需要提供联系人姓名和消息内容"
                return self._send_wechat_message(contact_name, message)
            elif action == "get_contacts":
                return self._get_wechat_contacts()
            else:
                return f"❌ 未知的微信操作: {action}"
        except Exception as e:
            return f"❌ 微信操作失败: {str(e)}"
    
    def _launch_wechat(self) -> str:
        """启动微信"""
        try:
            # 检查微信是否已经在运行
            desktop_state = self.desktop.get_state()
            for app in desktop_state.apps:
                if "微信" in app.name or "WeChat" in app.name:
                    return "✅ 微信已经在运行"
            
            # 尝试多种方式启动微信
            wechat_names = ["微信", "wechat", "WeChat", "WeChat.exe"]
            
            for name in wechat_names:
                try:
                    result, status = self.desktop.launch_app(name)
                    if status == 0:
                        # 等待微信启动
                        import time
                        time.sleep(5)
                        return f"✅ 成功启动微信: {result}"
                except Exception as e:
                    continue
            
            # 如果开始菜单方式失败，尝试直接启动exe
            try:
                result, status = self.desktop.execute_command("Start-Process 'WeChat.exe'")
                if status == 0:
                    import time
                    time.sleep(5)
                    return "✅ 通过直接启动成功启动微信"
            except Exception as e:
                pass
            
            # 尝试从常见路径启动
            common_paths = [
                "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe",
                "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe"
            ]
            
            for path in common_paths:
                try:
                    result, status = self.desktop.execute_command(f"if (Test-Path '{path}') {{ Start-Process '{path}'; 'success' }} else {{ 'not found' }}")
                    if "success" in result:
                        import time
                        time.sleep(5)
                        return f"✅ 通过路径启动微信: {path}"
                except Exception as e:
                    continue
            
            return "❌ 无法启动微信，请确保微信已安装"
            
        except Exception as e:
            return f"❌ 启动微信失败: {str(e)}"
    
    def _search_wechat_contact(self, contact_name: str) -> str:
        """在微信中搜索联系人"""
        try:
            # 获取当前桌面状态
            desktop_state = self.desktop.get_state()
            
            # 检查微信是否已打开
            wechat_open = False
            for app in desktop_state.apps:
                if "微信" in app.name or "WeChat" in app.name:
                    wechat_open = True
                    break
            
            if not wechat_open:
                return "❌ 微信未打开，请先启动微信"
            
            # 切换到微信窗口
            result, status = self.desktop.switch_app("微信")
            if status != 0:
                result, status = self.desktop.switch_app("WeChat")
            
            if status != 0:
                return "❌ 无法切换到微信窗口"
            
            # 等待微信界面加载
            import time
            time.sleep(2)
            
            # 点击搜索框（通常在微信窗口的左上角）
            # 这里使用相对坐标，因为微信窗口位置可能不同
            import pyautogui as pg
            
            # 获取微信窗口位置
            wechat_window = None
            for app in desktop_state.apps:
                if "微信" in app.name or "WeChat" in app.name:
                    wechat_window = app
                    break
            
            if wechat_window:
                # 计算搜索框的大概位置（微信搜索框通常在窗口左上角）
                search_x = wechat_window.size.width // 2  # 搜索框通常在窗口中央
                search_y = 50  # 距离顶部约50像素
                
                # 点击搜索框
                pg.click(search_x, search_y)
                time.sleep(1)
                
                # 输入联系人姓名
                pg.typewrite(contact_name, interval=0.1)
                time.sleep(1)
                
                # 按回车搜索
                pg.press('enter')
                time.sleep(2)
                
                return f"✅ 已搜索联系人: {contact_name}"
            else:
                return "❌ 无法找到微信窗口"
                
        except Exception as e:
            return f"❌ 搜索联系人失败: {str(e)}"
    
    def _send_wechat_message(self, contact_name: str, message: str) -> str:
        """发送微信消息"""
        try:
            # 先搜索联系人
            search_result = self._search_wechat_contact(contact_name)
            if "❌" in search_result:
                return search_result
            
            import time
            import pyautogui as pg
            
            # 等待搜索结果
            time.sleep(2)
            
            # 点击第一个搜索结果（通常是联系人）
            # 这里使用相对坐标点击搜索结果
            pg.click(pg.size().width // 2, pg.size().height // 2)
            time.sleep(1)
            
            # 点击消息输入框（通常在窗口底部）
            # 微信消息输入框通常在窗口底部中央
            input_x = pg.size().width // 2
            input_y = pg.size().height - 100  # 距离底部约100像素
            
            pg.click(input_x, input_y)
            time.sleep(1)
            
            # 输入消息内容
            pg.typewrite(message, interval=0.1)
            time.sleep(1)
            
            # 按回车发送
            pg.press('enter')
            
            return f"✅ 已向 {contact_name} 发送消息: {message}"
            
        except Exception as e:
            return f"❌ 发送消息失败: {str(e)}"
    
    def _get_wechat_contacts(self) -> str:
        """获取微信联系人列表"""
        try:
            # 获取当前桌面状态
            desktop_state = self.desktop.get_state()
            
            # 检查微信是否已打开
            wechat_open = False
            for app in desktop_state.apps:
                if "微信" in app.name or "WeChat" in app.name:
                    wechat_open = True
                    break
            
            if not wechat_open:
                return "❌ 微信未打开，请先启动微信"
            
            # 切换到微信窗口
            result, status = self.desktop.switch_app("微信")
            if status != 0:
                result, status = self.desktop.switch_app("WeChat")
            
            if status != 0:
                return "❌ 无法切换到微信窗口"
            
            # 等待微信界面加载
            import time
            time.sleep(2)
            
            # 这里可以添加获取联系人列表的逻辑
            # 由于微信的UI结构复杂，这里返回一个提示
            return "✅ 微信已打开，但获取联系人列表需要更复杂的UI操作"
            
        except Exception as e:
            return f"❌ 获取联系人列表失败: {str(e)}"
    
    async def _execute_tools(self, tool_calls: List[Any]) -> List[str]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            try:
                if function_name == "launch_app":
                    # 智能启动应用，自动尝试多种方法
                    result = self._smart_launch_app(arguments["name"].lower())
                    results.append(result)
                    
                elif function_name == "wechat_operation":
                    # 微信操作
                    action = arguments["action"]
                    contact_name = arguments.get("contact_name")
                    message = arguments.get("message")
                    result = self._wechat_operation(action, contact_name, message)
                    results.append(result)
                    
                elif function_name == "execute_command":
                    result, status_code = self.desktop.execute_command(arguments["command"])
                    results.append(f"PowerShell输出: {result}\n状态码: {status_code}")
                    
                elif function_name == "get_desktop_state":
                    use_vision = arguments.get("use_vision", False)
                    desktop_state = self.desktop.get_state(use_vision=use_vision)
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
                    control = self.desktop.get_element_under_cursor()
                    pg.click(x=x, y=y, button=button, clicks=clicks)
                    results.append(f"点击了 {control.Name} 元素在坐标 ({x}, {y})")
                    
                elif function_name == "type_text":
                    x, y = arguments["x"], arguments["y"]
                    text = arguments["text"]
                    clear = arguments.get("clear", False)
                    press_enter = arguments.get("press_enter", False)
                    
                    pg.click(x=x, y=y)
                    control = self.desktop.get_element_under_cursor()
                    
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
                        result, status = self.desktop.switch_app(app_name)
                        results.append(f"切换到应用: {result}")
                    elif action == "resize":
                        width = arguments.get("width")
                        height = arguments.get("height")
                        x = arguments.get("x")
                        y = arguments.get("y")
                        size_tuple = (width, height) if width and height else None
                        loc_tuple = (x, y) if x and y else None
                        result, _ = self.desktop.resize_app(size_tuple, loc_tuple)
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
                    
                elif function_name == "write_file_content":
                    file_path = arguments["file_path"]
                    content = arguments["content"]
                    encoding = arguments.get("encoding", "utf-8")
                    
                    try:
                        # 确保目录存在
                        import os
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # 写入文件
                        with open(file_path, 'w', encoding=encoding) as f:
                            f.write(content)
                        
                        results.append(f"✅ 成功写入文件: {file_path}\n内容长度: {len(content)} 字符")
                    except Exception as e:
                        results.append(f"❌ 写入文件失败: {str(e)}")
                    
                else:
                    results.append(f"未知工具: {function_name}")
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                results.append(f"执行工具 {function_name} 时出错: {str(e)}\n详细错误:\n{error_details}")
        
        return results
    
    async def _execute_tools_stream(self, tool_calls: List[Any], ui_callback) -> List[str]:
        """流式执行工具调用 - 实时显示执行过程，支持自主连续工作"""
        results = []
        
        for i, tool_call in enumerate(tool_calls):
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            try:
                # 显示正在执行的工具
                tool_display_name = self._get_tool_display_name(function_name)
                ui_callback.root.after(0, ui_callback.update_status, f"正在执行: {tool_display_name}")
                ui_callback.root.after(0, ui_callback.add_streaming_message, f"🔧 {tool_display_name}...", False)
                
                if function_name == "launch_app":
                    # 智能启动应用，自动尝试多种方法
                    result = self._smart_launch_app(arguments["name"].lower())
                    
                    # 根据结果显示不同的状态
                    if "成功" in result or "✅" in result:
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ {result}", False)
                        ui_callback.root.after(0, ui_callback.update_status, f"应用启动成功")
                    else:
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"⚠️ {result}", False)
                        ui_callback.root.after(0, ui_callback.update_status, f"应用启动遇到问题，将尝试其他方法")
                    
                    results.append(result)
                    
                elif function_name == "wechat_operation":
                    # 微信操作
                    action = arguments["action"]
                    contact_name = arguments.get("contact_name")
                    message = arguments.get("message")
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"💬 执行微信操作: {action}", False)
                    
                    result = self._wechat_operation(action, contact_name, message)
                    
                    # 根据结果显示不同的状态
                    if "成功" in result or "✅" in result:
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ {result}", False)
                        ui_callback.root.after(0, ui_callback.update_status, f"微信操作成功")
                    else:
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"⚠️ {result}", False)
                        ui_callback.root.after(0, ui_callback.update_status, f"微信操作遇到问题")
                    
                    results.append(result)
                    
                elif function_name == "execute_command":
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"💻 执行命令: {arguments['command']}", False)
                    result, status_code = self.desktop.execute_command(arguments["command"])
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"📋 输出: {result}", False)
                    results.append(f"PowerShell输出: {result}\n状态码: {status_code}")
                    
                elif function_name == "get_desktop_state":
                    ui_callback.root.after(0, ui_callback.add_streaming_message, "🖥️ 正在扫描桌面状态...", False)
                    use_vision = arguments.get("use_vision", False)
                    desktop_state = self.desktop.get_state(use_vision=use_vision)
                    interactive_elements = desktop_state.tree_state.interactive_elements_to_string()
                    informative_elements = desktop_state.tree_state.informative_elements_to_string()
                    apps = desktop_state.apps_to_string()
                    active_app = desktop_state.active_app_to_string()
                    
                    state_info = f"""当前桌面状态:
活动应用: {active_app}
打开的应用: {apps}
交互元素: {interactive_elements or '无'}
信息元素: {informative_elements or '无'}"""
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"📊 {state_info}", False)
                    results.append(state_info)
                    
                elif function_name == "click_element":
                    x, y = arguments["x"], arguments["y"]
                    button = arguments.get("button", "left")
                    clicks = arguments.get("clicks", 1)
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"🖱️ 点击坐标 ({x}, {y})", False)
                    pg.moveTo(x, y)
                    control = self.desktop.get_element_under_cursor()
                    pg.click(x=x, y=y, button=button, clicks=clicks)
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ 已点击 {control.Name}", False)
                    results.append(f"点击了 {control.Name} 元素在坐标 ({x}, {y})")
                    
                elif function_name == "type_text":
                    x, y = arguments["x"], arguments["y"]
                    text = arguments["text"]
                    clear = arguments.get("clear", False)
                    press_enter = arguments.get("press_enter", False)
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"⌨️ 输入文本: {text}", False)
                    pg.click(x=x, y=y)
                    control = self.desktop.get_element_under_cursor()
                    
                    if clear:
                        pg.hotkey('ctrl', 'a')
                        pg.press('backspace')
                    
                    pg.typewrite(text, interval=0.1)
                    
                    if press_enter:
                        pg.press('enter')
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ 已输入到 {control.Name}", False)
                    results.append(f"在 {control.Name} 元素输入了: {text}")
                    
                elif function_name == "scroll_window":
                    x, y = arguments["x"], arguments["y"]
                    direction = arguments["direction"]
                    wheel_times = arguments.get("wheel_times", 1)
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"🔄 滚动窗口 ({direction})", False)
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
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ 滚动完成", False)
                    results.append(f"在坐标 ({x}, {y}) 向{direction}滚动了{wheel_times}次")
                    
                elif function_name == "clipboard_operation":
                    operation = arguments["operation"]
                    if operation == "copy":
                        text = arguments["text"]
                        pc.copy(text)
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"📋 已复制: {text}", False)
                        results.append(f"已复制到剪贴板: {text}")
                    elif operation == "paste":
                        content = pc.paste()
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"📋 剪贴板内容: {content}", False)
                        results.append(f"剪贴板内容: {content}")
                        
                elif function_name == "window_management":
                    action = arguments["action"]
                    if action == "switch":
                        app_name = arguments["app_name"]
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"🔄 切换到应用: {app_name}", False)
                        result, status = self.desktop.switch_app(app_name)
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ {result}", False)
                        results.append(f"切换到应用: {result}")
                    elif action == "resize":
                        width = arguments.get("width")
                        height = arguments.get("height")
                        x = arguments.get("x")
                        y = arguments.get("y")
                        size_tuple = (width, height) if width and height else None
                        loc_tuple = (x, y) if x and y else None
                        result, _ = self.desktop.resize_app(size_tuple, loc_tuple)
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"📐 {result}", False)
                        results.append(f"窗口管理: {result}")
                        
                elif function_name == "keyboard_shortcut":
                    keys = arguments["keys"]
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"⌨️ 快捷键: {'+'.join(keys)}", False)
                    pg.hotkey(*keys)
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ 快捷键执行完成", False)
                    results.append(f"执行快捷键: {'+'.join(keys)}")
                    
                elif function_name == "scrape_webpage":
                    url = arguments["url"]
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"🌐 抓取网页: {url}", False)
                    response = requests.get(url, timeout=10)
                    from markdownify import markdownify
                    content = markdownify(html=response.text)
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"📄 网页内容已获取", False)
                    results.append(f"网页内容:\n{content[:500]}...")
                    
                elif function_name == "write_file_content":
                    file_path = arguments["file_path"]
                    content = arguments["content"]
                    encoding = arguments.get("encoding", "utf-8")
                    
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"📝 正在写入文件: {file_path}", False)
                    
                    try:
                        # 确保目录存在
                        import os
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # 写入文件
                        with open(file_path, 'w', encoding=encoding) as f:
                            f.write(content)
                        
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"✅ 文件写入成功！内容长度: {len(content)} 字符", False)
                        results.append(f"✅ 成功写入文件: {file_path}\n内容长度: {len(content)} 字符")
                    except Exception as e:
                        ui_callback.root.after(0, ui_callback.add_streaming_message, f"❌ 写入文件失败: {str(e)}", False)
                        results.append(f"❌ 写入文件失败: {str(e)}")
                    
                else:
                    ui_callback.root.after(0, ui_callback.add_streaming_message, f"❓ 未知工具: {function_name}", False)
                    results.append(f"未知工具: {function_name}")
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                error_msg = f"执行工具 {function_name} 时出错: {str(e)}"
                ui_callback.root.after(0, ui_callback.add_streaming_message, f"❌ {error_msg}", False)
                results.append(f"执行工具 {function_name} 时出错: {str(e)}\n详细错误:\n{error_details}")
        
        return results
    
    def _get_tool_display_name(self, function_name: str) -> str:
        """获取工具显示名称"""
        tool_names = {
            "launch_app": "启动应用程序",
            "wechat_operation": "微信操作",
            "execute_command": "执行命令",
            "get_desktop_state": "获取桌面状态",
            "click_element": "点击元素",
            "type_text": "输入文本",
            "scroll_window": "滚动窗口",
            "clipboard_operation": "剪贴板操作",
            "window_management": "窗口管理",
            "keyboard_shortcut": "键盘快捷键",
            "scrape_webpage": "网页抓取",
            "write_file_content": "写入文件内容"
        }
        return tool_names.get(function_name, function_name)

class SimpleFloatingBall:
    """简化版悬浮球"""
    
    def __init__(self, config: SimpleConfig):
        self.config = config
        self.root = None
        self.chat_window = None
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.qwen_client = SimpleQwenClient(config)
        
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
        
        # 状态指示器框架
        self.status_frame = tk.Frame(main_frame, bg=self.config.chat_bg_color)
        self.status_frame.pack(fill="x", pady=(0, 5))
        
        # 状态标签
        self.status_label = tk.Label(
            self.status_frame,
            text="",
            font=(self.config.font_family, self.config.font_size - 1),
            fg="#666666",
            bg=self.config.chat_bg_color
        )
        self.status_label.pack(side="left")
        
        # 动态状态指示器
        self.status_indicator = tk.Label(
            self.status_frame,
            text="",
            font=(self.config.font_family, 12),
            fg="#4A90E2",
            bg=self.config.chat_bg_color
        )
        self.status_indicator.pack(side="right")
        
        # 初始化状态
        self.is_working = False
        self.animation_id = None
        self.animation_frame = 0
        self.animation_symbols = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
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
        
        # 开始工作状态动画
        self.start_working_animation("正在分析任务...")
        
        # 异步获取AI响应
        threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()
        
    def get_ai_response(self, message: str):
        """获取AI响应"""
        try:
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 使用流式响应
            response = loop.run_until_complete(self.qwen_client.chat_stream(message, self))
            loop.close()
            
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
    
    def start_working_animation(self, status_text="正在工作"):
        """开始工作状态动画"""
        self.is_working = True
        self.status_label.config(text=status_text)
        self.animation_frame = 0
        self._animate_status()
    
    def stop_working_animation(self):
        """停止工作状态动画"""
        self.is_working = False
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self.status_label.config(text="")
        self.status_indicator.config(text="")
    
    def _animate_status(self):
        """状态动画循环"""
        if self.is_working:
            symbol = self.animation_symbols[self.animation_frame % len(self.animation_symbols)]
            self.status_indicator.config(text=symbol)
            self.animation_frame += 1
            self.animation_id = self.root.after(100, self._animate_status)
    
    def update_status(self, status_text):
        """更新状态文本"""
        self.status_label.config(text=status_text)
    
    def add_streaming_message(self, message: str, is_user: bool = True):
        """添加流式消息到聊天显示区域"""
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
        
    def run(self):
        """运行悬浮球"""
        self.create_floating_ball()
        self.root.mainloop()

def main():
    """主函数"""
    print("=" * 50)
    print("桌面AI助手 - 增强版")
    print("=" * 50)
    
    # 创建配置
    config = SimpleConfig()
    
    print(f"使用模型: {config.model}")
    print(f"API地址: {config.base_url}")
    print("\n启动悬浮球AI助手...")
    print("双击悬浮球打开对话窗口")
    print("拖拽悬浮球可以移动位置")
    print("AI助手现在可以直接执行本地操作！")
    print("支持：启动应用、执行命令、点击操作、文本输入等")
    print("按Ctrl+C退出程序")
    
    # 创建并运行悬浮球
    ball = SimpleFloatingBall(config)
    
    try:
        ball.run()
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

if __name__ == "__main__":
    main()
