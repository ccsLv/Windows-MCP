#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件启动器模块 - 实现统一的软件调用工作流程
"""

import time
import pyautogui as pg
import uiautomation as ua
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# 设置pyautogui参数
pg.FAILSAFE = False
pg.PAUSE = 0.5

class LaunchStatus(Enum):
    """启动状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"

@dataclass
class LaunchResult:
    """启动结果数据类"""
    status: LaunchStatus
    message: str
    app_name: str
    execution_time: float
    method_used: str = ""

class SoftwareLauncher:
    """软件启动器类 - 实现统一的软件调用工作流程"""
    
    def __init__(self):
        self.search_box_coords = None
        self.search_results_coords = None
        self.best_match_coords = None
        self.launch_methods = [
            self._launch_via_search_box,
            self._launch_via_powershell,
            self._launch_via_run_dialog,
            self._launch_via_start_menu,
            self._launch_via_desktop_shortcut,
            self._launch_via_file_explorer
        ]
    
    def launch_software(self, software_name: str, timeout: int = 30) -> LaunchResult:
        """
        启动软件的主要方法
        
        Args:
            software_name: 软件名称
            timeout: 超时时间（秒）
            
        Returns:
            LaunchResult: 启动结果
        """
        start_time = time.time()
        
        print(f"🚀 开始启动软件: {software_name}")
        
        # 尝试多种启动方法
        for i, method in enumerate(self.launch_methods, 1):
            try:
                print(f"🔧 尝试方法 {i}: {method.__name__}")
                result = method(software_name, timeout)
                
                if result.status == LaunchStatus.SUCCESS:
                    execution_time = time.time() - start_time
                    result.execution_time = execution_time
                    result.method_used = method.__name__
                    print(f"✅ 成功启动 {software_name} (方法: {method.__name__}, 耗时: {execution_time:.2f}s)")
                    return result
                else:
                    print(f"❌ 方法 {i} 失败: {result.message}")
                    
            except Exception as e:
                print(f"❌ 方法 {i} 异常: {str(e)}")
                continue
        
        # 所有方法都失败
        execution_time = time.time() - start_time
        return LaunchResult(
            status=LaunchStatus.FAILED,
            message=f"所有启动方法都失败了，无法启动 {software_name}",
            app_name=software_name,
            execution_time=execution_time,
            method_used="all_methods_failed"
        )
    
    def _launch_via_search_box(self, software_name: str, timeout: int) -> LaunchResult:
        """通过搜索框启动软件（主要方法）"""
        try:
            # 1. 点击桌面下方的搜索框
            if not self._click_search_box():
                return LaunchResult(LaunchStatus.FAILED, "无法找到搜索框", software_name, 0)
            
            time.sleep(1)
            
            # 2. 在输入框中输入软件名称
            if not self._type_software_name(software_name):
                return LaunchResult(LaunchStatus.FAILED, "无法输入软件名称", software_name, 0)
            
            time.sleep(2)
            
            # 3. 在上拉界面中找到最佳适配的软件
            if not self._find_best_match(software_name):
                return LaunchResult(LaunchStatus.NOT_FOUND, f"未找到软件 {software_name}", software_name, 0)
            
            time.sleep(1)
            
            # 4. 点击最佳适配的软件
            if not self._click_best_match():
                return LaunchResult(LaunchStatus.FAILED, "无法点击软件", software_name, 0)
            
            # 5. 等待软件启动
            if self._wait_for_app_launch(software_name, timeout):
                return LaunchResult(LaunchStatus.SUCCESS, f"成功启动 {software_name}", software_name, 0)
            else:
                return LaunchResult(LaunchStatus.TIMEOUT, f"启动 {software_name} 超时", software_name, 0)
                
        except Exception as e:
            return LaunchResult(LaunchStatus.FAILED, f"启动过程中出错: {str(e)}", software_name, 0)
    
    def _click_search_box(self) -> bool:
        """点击桌面下方的搜索框"""
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = pg.size()
            
            # 搜索框通常位于任务栏中央，高度约为屏幕高度的95%
            search_box_x = screen_width // 2
            search_box_y = int(screen_height * 0.95)
            
            # 点击搜索框
            pg.click(search_box_x, search_box_y)
            self.search_box_coords = (search_box_x, search_box_y)
            
            print(f"✅ 已点击搜索框位置: ({search_box_x}, {search_box_y})")
            return True
            
        except Exception as e:
            print(f"❌ 点击搜索框失败: {str(e)}")
            return False
    
    def _type_software_name(self, software_name: str) -> bool:
        """在搜索框中输入软件名称"""
        try:
            # 清空搜索框并输入软件名称
            pg.hotkey('ctrl', 'a')  # 全选
            pg.press('backspace')   # 删除
            pg.typewrite(software_name, interval=0.1)
            
            print(f"✅ 已输入软件名称: {software_name}")
            return True
            
        except Exception as e:
            print(f"❌ 输入软件名称失败: {str(e)}")
            return False
    
    def _find_best_match(self, software_name: str) -> bool:
        """在上拉界面中找到最佳适配的软件"""
        try:
            time.sleep(1)  # 等待搜索结果出现
            
            # 获取搜索结果区域
            search_results = ua.FindFirstControl(ua.ControlType.WindowControl, 
                                               lambda c: "搜索" in c.Name or "Search" in c.Name)
            
            if not search_results:
                # 尝试查找开始菜单搜索结果
                search_results = ua.FindFirstControl(ua.ControlType.WindowControl,
                                                   lambda c: "开始" in c.Name or "Start" in c.Name)
            
            if not search_results:
                print("❌ 未找到搜索结果窗口")
                return False
            
            # 查找最佳匹配项
            best_match = None
            max_similarity = 0
            
            # 查找所有可能的匹配项
            for control in search_results.GetChildren():
                if control.ControlTypeName == "ListItemControl" or control.ControlTypeName == "ButtonControl":
                    control_name = control.Name.lower()
                    target_name = software_name.lower()
                    
                    # 计算相似度
                    similarity = self._calculate_similarity(control_name, target_name)
                    
                    if similarity > max_similarity and similarity > 0.3:  # 相似度阈值
                        max_similarity = similarity
                        best_match = control
            
            if best_match:
                # 获取最佳匹配项的坐标
                rect = best_match.BoundingRectangle
                self.best_match_coords = (rect.left + rect.width // 2, rect.top + rect.height // 2)
                print(f"✅ 找到最佳匹配: {best_match.Name} (相似度: {max_similarity:.2f})")
                return True
            else:
                print(f"❌ 未找到匹配的软件: {software_name}")
                return False
                
        except Exception as e:
            print(f"❌ 查找最佳匹配失败: {str(e)}")
            return False
    
    def _click_best_match(self) -> bool:
        """点击最佳适配的软件"""
        try:
            if not self.best_match_coords:
                print("❌ 没有找到最佳匹配坐标")
                return False
            
            x, y = self.best_match_coords
            pg.click(x, y)
            
            print(f"✅ 已点击最佳匹配位置: ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ 点击最佳匹配失败: {str(e)}")
            return False
    
    def _wait_for_app_launch(self, software_name: str, timeout: int) -> bool:
        """等待应用程序启动"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查是否有新的应用程序窗口出现
                windows = ua.GetRootControl().GetChildren()
                
                for window in windows:
                    if window.ControlTypeName == "WindowControl":
                        window_name = window.Name.lower()
                        target_name = software_name.lower()
                        
                        # 检查窗口名称是否包含软件名称
                        if (target_name in window_name or 
                            any(keyword in window_name for keyword in target_name.split())):
                            print(f"✅ 检测到应用程序窗口: {window.Name}")
                            return True
                
                time.sleep(1)
            
            print(f"❌ 等待应用程序启动超时: {timeout}秒")
            return False
            
        except Exception as e:
            print(f"❌ 等待应用程序启动时出错: {str(e)}")
            return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 简单的相似度计算（可以改进为更复杂的算法）
        str1 = str1.lower()
        str2 = str2.lower()
        
        # 完全匹配
        if str1 == str2:
            return 1.0
        
        # 包含关系
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # 计算公共子序列
        common_chars = set(str1) & set(str2)
        if not common_chars:
            return 0.0
        
        # 计算相似度
        similarity = len(common_chars) / max(len(str1), len(str2))
        return similarity
    
    def _launch_via_powershell(self, software_name: str, timeout: int) -> LaunchResult:
        """通过PowerShell启动软件（备用方法1）"""
        try:
            import subprocess
            
            # 尝试通过PowerShell启动
            cmd = f'Start-Process "{software_name}"'
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                return LaunchResult(LaunchStatus.SUCCESS, f"通过PowerShell启动 {software_name}", software_name, 0)
            else:
                return LaunchResult(LaunchStatus.FAILED, f"PowerShell启动失败: {result.stderr}", software_name, 0)
                
        except Exception as e:
            return LaunchResult(LaunchStatus.FAILED, f"PowerShell启动异常: {str(e)}", software_name, 0)
    
    def _launch_via_run_dialog(self, software_name: str, timeout: int) -> LaunchResult:
        """通过运行对话框启动软件（备用方法2）"""
        try:
            # 打开运行对话框
            pg.hotkey('win', 'r')
            time.sleep(1)
            
            # 输入软件名称
            pg.typewrite(software_name)
            time.sleep(1)
            
            # 按回车
            pg.press('enter')
            time.sleep(2)
            
            return LaunchResult(LaunchStatus.SUCCESS, f"通过运行对话框启动 {software_name}", software_name, 0)
            
        except Exception as e:
            return LaunchResult(LaunchStatus.FAILED, f"运行对话框启动异常: {str(e)}", software_name, 0)
    
    def _launch_via_start_menu(self, software_name: str, timeout: int) -> LaunchResult:
        """通过开始菜单启动软件（备用方法3）"""
        try:
            # 打开开始菜单
            pg.press('win')
            time.sleep(1)
            
            # 输入软件名称
            pg.typewrite(software_name)
            time.sleep(2)
            
            # 按回车
            pg.press('enter')
            time.sleep(2)
            
            return LaunchResult(LaunchStatus.SUCCESS, f"通过开始菜单启动 {software_name}", software_name, 0)
            
        except Exception as e:
            return LaunchResult(LaunchStatus.FAILED, f"开始菜单启动异常: {str(e)}", software_name, 0)
    
    def _launch_via_desktop_shortcut(self, software_name: str, timeout: int) -> LaunchResult:
        """通过桌面快捷方式启动软件（备用方法4）"""
        try:
            # 切换到桌面
            pg.hotkey('win', 'd')
            time.sleep(1)
            
            # 查找桌面快捷方式
            desktop = ua.GetRootControl().GetFirstChildControl(lambda c: c.Name == "Desktop")
            if not desktop:
                return LaunchResult(LaunchStatus.NOT_FOUND, "未找到桌面", software_name, 0)
            
            # 查找匹配的快捷方式
            shortcut = desktop.FindFirstChildControl(
                lambda c: software_name.lower() in c.Name.lower() and 
                         c.ControlTypeName == "ButtonControl"
            )
            
            if shortcut:
                rect = shortcut.BoundingRectangle
                pg.click(rect.left + rect.width // 2, rect.top + rect.height // 2)
                time.sleep(2)
                return LaunchResult(LaunchStatus.SUCCESS, f"通过桌面快捷方式启动 {software_name}", software_name, 0)
            else:
                return LaunchResult(LaunchStatus.NOT_FOUND, f"未找到 {software_name} 的桌面快捷方式", software_name, 0)
                
        except Exception as e:
            return LaunchResult(LaunchStatus.FAILED, f"桌面快捷方式启动异常: {str(e)}", software_name, 0)
    
    def _launch_via_file_explorer(self, software_name: str, timeout: int) -> LaunchResult:
        """通过文件资源管理器启动软件（备用方法5）"""
        try:
            # 打开文件资源管理器
            pg.hotkey('win', 'e')
            time.sleep(2)
            
            # 导航到程序文件目录
            pg.hotkey('ctrl', 'l')  # 定位到地址栏
            time.sleep(1)
            
            # 输入程序文件路径
            program_paths = [
                r"C:\Program Files",
                r"C:\Program Files (x86)",
                r"C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps"
            ]
            
            for path in program_paths:
                try:
                    pg.typewrite(path)
                    pg.press('enter')
                    time.sleep(2)
                    
                    # 搜索软件
                    pg.hotkey('ctrl', 'f')
                    time.sleep(1)
                    pg.typewrite(software_name)
                    time.sleep(2)
                    
                    # 查找匹配项并双击
                    # 这里需要更复杂的逻辑来查找和点击匹配的文件
                    break
                    
                except:
                    continue
            
            return LaunchResult(LaunchStatus.SUCCESS, f"通过文件资源管理器启动 {software_name}", software_name, 0)
            
        except Exception as e:
            return LaunchResult(LaunchStatus.FAILED, f"文件资源管理器启动异常: {str(e)}", software_name, 0)

# 测试函数
def test_software_launcher():
    """测试软件启动器"""
    launcher = SoftwareLauncher()
    
    # 测试启动记事本
    result = launcher.launch_software("notepad")
    print(f"启动结果: {result}")
    
    # 测试启动计算器
    result = launcher.launch_software("calculator")
    print(f"启动结果: {result}")

if __name__ == "__main__":
    test_software_launcher()
