#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QQ启动功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_start import SimpleConfig, SimpleQwenClient

def test_qq_launch():
    """测试QQ启动功能"""
    print("=" * 60)
    print("测试QQ启动功能")
    print("=" * 60)
    
    # 创建配置
    config = SimpleConfig()
    
    # 创建AI客户端
    client = SimpleQwenClient(config)
    
    print("测试智能启动QQ...")
    
    # 测试QQ启动
    result = client._smart_launch_app("qq")
    print(f"启动结果: {result}")
    
    print("\n" + "=" * 60)
    print("修复说明：")
    print("1. 添加了QQ到应用名称映射")
    print("2. 增强了系统提示，强制使用工具")
    print("3. 优化了继续判断机制")
    print("4. 现在AI应该能直接启动QQ，而不是提供手动指导")
    print("=" * 60)

if __name__ == "__main__":
    test_qq_launch()
