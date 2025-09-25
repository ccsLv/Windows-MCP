#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件打开场景的修复
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_start import SimpleConfig, SimpleQwenClient

def test_file_opening_scenario():
    """测试文件打开场景的修复"""
    print("=" * 60)
    print("测试文件打开场景的修复")
    print("=" * 60)
    
    # 创建配置
    config = SimpleConfig()
    
    # 创建AI客户端
    client = SimpleQwenClient(config)
    
    # 模拟对话历史
    client.conversation_history = [
        {"role": "user", "content": "打开桌面的语音文本.xls"},
        {"role": "assistant", "content": "我理解您想打开位于桌面的语音文本.xls文件,但目前遇到了一些技术限制。让我尝试另一种方法。我可以先确认一下这个文件是否真的存在于桌面上。通常桌面文件位于当前用户的Desktop目录下。让我尝试通过PowerShell检查该文件是否存在..."}
    ]
    
    # 测试继续判断
    tool_results = []  # 模拟没有工具调用结果
    original_message = "打开桌面的语音文本.xls"
    
    should_continue = client._should_continue_working(tool_results, original_message)
    
    print(f"原始消息: {original_message}")
    print(f"最后一条助手消息: {client.conversation_history[-1]['content']}")
    print(f"是否应该继续: {should_continue}")
    
    if should_continue:
        print("✅ 修复成功！AI会继续执行PowerShell命令")
    else:
        print("❌ 修复失败！AI仍然会停下来等待用户确认")
    
    print("\n" + "=" * 60)
    print("修复说明：")
    print("1. 增强了继续判断关键词，包括'让我尝试'、'技术限制'等")
    print("2. 更新了系统提示，强调遇到问题时立即执行工具调用")
    print("3. 添加了关键行为准则，确保AI不会停下来等待")
    print("=" * 60)

if __name__ == "__main__":
    test_file_opening_scenario()
