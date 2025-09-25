#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版微信操作模块
使用更精确的UI自动化技术
"""

import pyautogui as pg
import uiautomation as ua
import time
import subprocess
import os
from typing import Optional, Tuple

class WeChatEnhanced:
    """增强版微信操作类"""
    
    def __init__(self):
        # 配置pyautogui
        pg.FAILSAFE = False
        pg.PAUSE = 0.5
        
        # 微信窗口句柄
        self.wechat_window = None
        self.wechat_process = None
        
    def launch_wechat(self) -> Tuple[str, bool]:
        """启动微信"""
        try:
            # 检查微信是否已经在运行
            if self._is_wechat_running():
                return "✅ 微信已经在运行", True
            
            # 尝试多种方式启动微信
            wechat_paths = [
                "WeChat.exe",
                "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe",
                "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe",
                os.path.expanduser("~\\AppData\\Local\\Tencent\\WeChat\\WeChat.exe")
            ]
            
            for path in wechat_paths:
                try:
                    if os.path.exists(path):
                        subprocess.Popen([path], shell=True)
                        time.sleep(5)  # 等待微信启动
                        
                        if self._is_wechat_running():
                            return f"✅ 成功启动微信: {path}", True
                    else:
                        # 尝试从开始菜单启动
                        subprocess.run(["powershell", "-Command", f"Start-Process '{path}'"], 
                                     capture_output=True, timeout=10)
                        time.sleep(5)
                        
                        if self._is_wechat_running():
                            return f"✅ 通过开始菜单启动微信", True
                except Exception as e:
                    continue
            
            return "❌ 无法启动微信，请确保微信已安装", False
            
        except Exception as e:
            return f"❌ 启动微信失败: {str(e)}", False
    
    def _is_wechat_running(self) -> bool:
        """检查微信是否在运行"""
        try:
            # 查找微信窗口
            wechat_windows = ua.FindWindows(ClassName="WeChatMainWndForPC")
            if wechat_windows:
                self.wechat_window = wechat_windows[0]
                return True
            
            # 也检查其他可能的微信窗口类名
            wechat_windows = ua.FindWindows(Name="微信")
            if wechat_windows:
                self.wechat_window = wechat_windows[0]
                return True
                
            return False
        except Exception:
            return False
    
    def search_contact(self, contact_name: str) -> Tuple[str, bool]:
        """搜索联系人"""
        try:
            if not self._is_wechat_running():
                return "❌ 微信未运行，请先启动微信", False
            
            # 确保微信窗口在前台
            if self.wechat_window:
                self.wechat_window.SetFocus()
                time.sleep(1)
            
            # 查找搜索框
            search_box = self._find_search_box()
            if not search_box:
                return "❌ 无法找到微信搜索框", False
            
            # 点击搜索框
            search_box.Click()
            time.sleep(1)
            
            # 清空搜索框
            pg.hotkey('ctrl', 'a')
            pg.press('delete')
            time.sleep(0.5)
            
            # 输入联系人姓名
            pg.typewrite(contact_name, interval=0.1)
            time.sleep(1)
            
            # 按回车搜索
            pg.press('enter')
            time.sleep(2)
            
            return f"✅ 已搜索联系人: {contact_name}", True
            
        except Exception as e:
            return f"❌ 搜索联系人失败: {str(e)}", False
    
    def _find_search_box(self) -> Optional[ua.Control]:
        """查找微信搜索框"""
        try:
            if not self.wechat_window:
                return None
            
            # 查找搜索框控件
            search_box = self.wechat_window.FindFirstChild(
                ControlType=ua.ControlType.EditControl,
                Name="搜索"
            )
            
            if search_box:
                return search_box
            
            # 如果没找到，尝试其他可能的搜索框
            search_box = self.wechat_window.FindFirstChild(
                ControlType=ua.ControlType.EditControl
            )
            
            return search_box
            
        except Exception:
            return None
    
    def send_message(self, contact_name: str, message: str) -> Tuple[str, bool]:
        """发送消息"""
        try:
            # 先搜索联系人
            search_result, success = self.search_contact(contact_name)
            if not success:
                return search_result, False
            
            # 等待搜索结果
            time.sleep(2)
            
            # 点击第一个搜索结果（联系人）
            self._click_first_search_result()
            time.sleep(2)
            
            # 查找消息输入框
            input_box = self._find_message_input_box()
            if not input_box:
                return "❌ 无法找到消息输入框", False
            
            # 点击输入框
            input_box.Click()
            time.sleep(1)
            
            # 清空输入框
            pg.hotkey('ctrl', 'a')
            pg.press('delete')
            time.sleep(0.5)
            
            # 输入消息
            pg.typewrite(message, interval=0.1)
            time.sleep(1)
            
            # 发送消息
            pg.press('enter')
            time.sleep(1)
            
            return f"✅ 已向 {contact_name} 发送消息: {message}", True
            
        except Exception as e:
            return f"❌ 发送消息失败: {str(e)}", False
    
    def _click_first_search_result(self):
        """点击第一个搜索结果"""
        try:
            # 获取屏幕中心位置，通常搜索结果在屏幕中央
            screen_width, screen_height = pg.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            # 点击搜索结果区域
            pg.click(center_x, center_y - 100)  # 稍微向上一点
            
        except Exception as e:
            print(f"点击搜索结果失败: {e}")
    
    def _find_message_input_box(self) -> Optional[ua.Control]:
        """查找消息输入框"""
        try:
            if not self.wechat_window:
                return None
            
            # 查找消息输入框
            input_box = self.wechat_window.FindFirstChild(
                ControlType=ua.ControlType.EditControl,
                Name=""
            )
            
            if input_box:
                return input_box
            
            # 如果没找到，尝试查找所有编辑框
            edit_controls = self.wechat_window.FindAllChildren(
                ControlType=ua.ControlType.EditControl
            )
            
            # 返回最后一个编辑框（通常是消息输入框）
            if edit_controls:
                return edit_controls[-1]
            
            return None
            
        except Exception:
            return None
    
    def get_contacts(self) -> Tuple[str, bool]:
        """获取联系人列表"""
        try:
            if not self._is_wechat_running():
                return "❌ 微信未运行，请先启动微信", False
            
            # 这里可以实现获取联系人列表的逻辑
            # 由于微信的UI结构复杂，这里返回一个提示
            return "✅ 微信已打开，获取联系人列表功能需要进一步开发", True
            
        except Exception as e:
            return f"❌ 获取联系人列表失败: {str(e)}", False

def test_wechat_enhanced():
    """测试增强版微信功能"""
    print("=" * 50)
    print("测试增强版微信功能")
    print("=" * 50)
    
    wechat = WeChatEnhanced()
    
    # 测试启动微信
    print("1. 测试启动微信...")
    result, success = wechat.launch_wechat()
    print(f"   结果: {result}")
    
    if success:
        print("2. 测试搜索联系人...")
        result, success = wechat.search_contact("方志豪")
        print(f"   结果: {result}")
        
        if success:
            print("3. 测试发送消息...")
            result, success = wechat.send_message("方志豪", "白老师，你过来一下")
            print(f"   结果: {result}")
    
    print("\n✨ 增强版微信功能测试完成！")

if __name__ == "__main__":
    test_wechat_enhanced()
