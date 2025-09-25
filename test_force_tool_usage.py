#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试强制工具使用
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_start import SimpleConfig, SimpleQwenClient

class MockUICallback:
    """模拟UI回调"""
    def __init__(self):
        self.messages = []
        self.status = ""
        self.root = self  # 添加root属性
    
    def add_streaming_message(self, message, is_user):
        self.messages.append(("user" if is_user else "ai", message))
        print(f"[{'用户' if is_user else 'AI助手'}]: {message}")
    
    def update_status(self, status):
        self.status = status
        print(f"[状态]: {status}")
    
    def start_working_animation(self, text):
        print(f"[工作动画]: {text}")
    
    def stop_working_animation(self):
        print("[工作动画]: 停止")
    
    def after(self, delay, func, *args):
        """模拟tkinter的after方法"""
        func(*args)

async def test_force_tool_usage():
    """测试强制工具使用"""
    print("=" * 60)
    print("测试强制工具使用")
    print("=" * 60)
    
    # 创建配置
    config = SimpleConfig()
    
    # 创建AI客户端
    client = SimpleQwenClient(config)
    
    # 创建模拟UI回调
    ui_callback = MockUICallback()
    
    print("测试场景：用户说'打开QQ'")
    print("预期：AI必须调用launch_app工具，不能只回复文本")
    print()
    
    try:
        # 测试聊天
        await client.chat_stream("打开QQ", ui_callback)
        
        # 检查是否有工具调用
        has_tool_calls = False
        for msg in client.conversation_history:
            if "tool_calls" in msg:
                has_tool_calls = True
                print(f"✅ 发现工具调用: {msg['tool_calls']}")
                break
        
        if has_tool_calls:
            print("✅ 测试通过！AI正确使用了工具")
        else:
            print("❌ 测试失败！AI没有使用工具，只回复了文本")
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_force_tool_usage())
