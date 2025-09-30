#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流程管理器 - 处理不同软件的操作流程
"""

import time
import pyautogui as pg
import uiautomation as ua
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

# 设置pyautogui参数
pg.FAILSAFE = False
pg.PAUSE = 0.5

class WorkflowStatus(Enum):
    """工作流程状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """工作流程步骤数据类"""
    name: str
    description: str
    action: Callable
    timeout: int = 10
    retry_count: int = 3
    required: bool = True

@dataclass
class WorkflowResult:
    """工作流程结果数据类"""
    status: WorkflowStatus
    message: str
    steps_completed: int
    total_steps: int
    execution_time: float
    error_details: Optional[str] = None

class SoftwareWorkflowManager:
    """软件工作流程管理器"""
    
    def __init__(self):
        self.workflows = {}
        self.current_workflow = None
        self._load_workflow_configs()
    
    def _load_workflow_configs(self):
        """加载工作流程配置"""
        # 预定义的工作流程配置
        self.workflows = {
            "wechat": {
                "name": "微信操作流程",
                "description": "启动微信并执行相关操作",
                "steps": [
                    {
                        "name": "launch_wechat",
                        "description": "启动微信",
                        "action": "launch_software",
                        "params": {"software_name": "微信"},
                        "timeout": 30,
                        "required": True
                    },
                    {
                        "name": "wait_for_login",
                        "description": "等待微信登录界面",
                        "action": "wait_for_element",
                        "params": {"element_type": "login_interface"},
                        "timeout": 15,
                        "required": True
                    },
                    {
                        "name": "click_login",
                        "description": "点击登录按钮",
                        "action": "click_login_button",
                        "params": {},
                        "timeout": 5,
                        "required": False
                    }
                ]
            },
            "chrome": {
                "name": "Chrome浏览器操作流程",
                "description": "启动Chrome并执行相关操作",
                "steps": [
                    {
                        "name": "launch_chrome",
                        "description": "启动Chrome浏览器",
                        "action": "launch_software",
                        "params": {"software_name": "chrome"},
                        "timeout": 30,
                        "required": True
                    },
                    {
                        "name": "wait_for_browser",
                        "description": "等待浏览器加载完成",
                        "action": "wait_for_element",
                        "params": {"element_type": "browser_ready"},
                        "timeout": 15,
                        "required": True
                    },
                    {
                        "name": "navigate_to_url",
                        "description": "导航到指定URL",
                        "action": "navigate_to_url",
                        "params": {"url": ""},
                        "timeout": 10,
                        "required": False
                    }
                ]
            },
            "notepad": {
                "name": "记事本操作流程",
                "description": "启动记事本并执行相关操作",
                "steps": [
                    {
                        "name": "launch_notepad",
                        "description": "启动记事本",
                        "action": "launch_software",
                        "params": {"software_name": "notepad"},
                        "timeout": 30,
                        "required": True
                    },
                    {
                        "name": "wait_for_editor",
                        "description": "等待记事本编辑器加载",
                        "action": "wait_for_element",
                        "params": {"element_type": "text_editor"},
                        "timeout": 10,
                        "required": True
                    },
                    {
                        "name": "type_text",
                        "description": "输入文本内容",
                        "action": "type_text",
                        "params": {"text": ""},
                        "timeout": 5,
                        "required": False
                    }
                ]
            },
            "calculator": {
                "name": "计算器操作流程",
                "description": "启动计算器并执行相关操作",
                "steps": [
                    {
                        "name": "launch_calculator",
                        "description": "启动计算器",
                        "action": "launch_software",
                        "params": {"software_name": "calculator"},
                        "timeout": 30,
                        "required": True
                    },
                    {
                        "name": "wait_for_calculator",
                        "description": "等待计算器界面加载",
                        "action": "wait_for_element",
                        "params": {"element_type": "calculator_interface"},
                        "timeout": 10,
                        "required": True
                    },
                    {
                        "name": "perform_calculation",
                        "description": "执行计算操作",
                        "action": "perform_calculation",
                        "params": {"expression": ""},
                        "timeout": 5,
                        "required": False
                    }
                ]
            }
        }
    
    def execute_workflow(self, workflow_name: str, custom_params: Dict[str, Any] = None) -> WorkflowResult:
        """
        执行指定的工作流程
        
        Args:
            workflow_name: 工作流程名称
            custom_params: 自定义参数
            
        Returns:
            WorkflowResult: 执行结果
        """
        if workflow_name not in self.workflows:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                message=f"未找到工作流程: {workflow_name}",
                steps_completed=0,
                total_steps=0,
                execution_time=0,
                error_details=f"可用工作流程: {list(self.workflows.keys())}"
            )
        
        workflow_config = self.workflows[workflow_name]
        start_time = time.time()
        
        print(f"🚀 开始执行工作流程: {workflow_config['name']}")
        print(f"📝 描述: {workflow_config['description']}")
        
        self.current_workflow = workflow_name
        steps_completed = 0
        total_steps = len(workflow_config['steps'])
        
        try:
            for i, step_config in enumerate(workflow_config['steps'], 1):
                print(f"\n📋 步骤 {i}/{total_steps}: {step_config['name']}")
                print(f"📄 描述: {step_config['description']}")
                
                # 合并自定义参数
                step_params = step_config['params'].copy()
                if custom_params:
                    step_params.update(custom_params)
                
                # 执行步骤
                step_result = self._execute_step(step_config, step_params)
                
                if step_result['success']:
                    steps_completed += 1
                    print(f"✅ 步骤 {i} 完成: {step_result['message']}")
                else:
                    print(f"❌ 步骤 {i} 失败: {step_result['message']}")
                    
                    if step_config.get('required', True):
                        execution_time = time.time() - start_time
                        return WorkflowResult(
                            status=WorkflowStatus.FAILED,
                            message=f"工作流程在步骤 {i} 失败",
                            steps_completed=steps_completed,
                            total_steps=total_steps,
                            execution_time=execution_time,
                            error_details=step_result['message']
                        )
                    else:
                        print(f"⚠️ 步骤 {i} 不是必需的，继续执行...")
            
            execution_time = time.time() - start_time
            print(f"\n🎉 工作流程执行完成！总耗时: {execution_time:.2f}秒")
            
            return WorkflowResult(
                status=WorkflowStatus.COMPLETED,
                message=f"工作流程 {workflow_config['name']} 执行成功",
                steps_completed=steps_completed,
                total_steps=total_steps,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                message=f"工作流程执行异常: {str(e)}",
                steps_completed=steps_completed,
                total_steps=total_steps,
                execution_time=execution_time,
                error_details=str(e)
            )
        finally:
            self.current_workflow = None
    
    def _execute_step(self, step_config: Dict, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        action = step_config['action']
        timeout = step_config.get('timeout', 10)
        
        try:
            if action == "launch_software":
                return self._launch_software_step(params, timeout)
            elif action == "wait_for_element":
                return self._wait_for_element_step(params, timeout)
            elif action == "click_login_button":
                return self._click_login_button_step(params, timeout)
            elif action == "navigate_to_url":
                return self._navigate_to_url_step(params, timeout)
            elif action == "type_text":
                return self._type_text_step(params, timeout)
            elif action == "perform_calculation":
                return self._perform_calculation_step(params, timeout)
            else:
                return {
                    'success': False,
                    'message': f"未知的操作类型: {action}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"执行步骤时出错: {str(e)}"
            }
    
    def _launch_software_step(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """启动软件步骤"""
        from .software_launcher import SoftwareLauncher
        
        software_name = params.get('software_name', '')
        if not software_name:
            return {'success': False, 'message': '未指定软件名称'}
        
        launcher = SoftwareLauncher()
        result = launcher.launch_software(software_name, timeout)
        
        return {
            'success': result.status.value == 'success',
            'message': result.message
        }
    
    def _wait_for_element_step(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """等待元素步骤"""
        element_type = params.get('element_type', '')
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if element_type == "login_interface":
                    # 查找微信登录界面
                    if self._find_wechat_login_interface():
                        return {'success': True, 'message': '找到登录界面'}
                elif element_type == "browser_ready":
                    # 查找浏览器就绪状态
                    if self._find_browser_ready():
                        return {'success': True, 'message': '浏览器已就绪'}
                elif element_type == "text_editor":
                    # 查找文本编辑器
                    if self._find_text_editor():
                        return {'success': True, 'message': '找到文本编辑器'}
                elif element_type == "calculator_interface":
                    # 查找计算器界面
                    if self._find_calculator_interface():
                        return {'success': True, 'message': '找到计算器界面'}
                
                time.sleep(1)
                
            except Exception as e:
                return {'success': False, 'message': f'等待元素时出错: {str(e)}'}
        
        return {'success': False, 'message': f'等待 {element_type} 超时'}
    
    def _click_login_button_step(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """点击登录按钮步骤"""
        try:
            # 查找微信登录按钮
            login_button = ua.FindFirstControl(
                ua.ControlType.ButtonControl,
                lambda c: "登录" in c.Name or "Login" in c.Name
            )
            
            if login_button:
                rect = login_button.BoundingRectangle
                pg.click(rect.left + rect.width // 2, rect.top + rect.height // 2)
                return {'success': True, 'message': '已点击登录按钮'}
            else:
                return {'success': False, 'message': '未找到登录按钮'}
                
        except Exception as e:
            return {'success': False, 'message': f'点击登录按钮时出错: {str(e)}'}
    
    def _navigate_to_url_step(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """导航到URL步骤"""
        url = params.get('url', '')
        if not url:
            return {'success': False, 'message': '未指定URL'}
        
        try:
            # 点击地址栏
            pg.hotkey('ctrl', 'l')
            time.sleep(1)
            
            # 输入URL
            pg.typewrite(url)
            time.sleep(1)
            
            # 按回车
            pg.press('enter')
            time.sleep(2)
            
            return {'success': True, 'message': f'已导航到 {url}'}
            
        except Exception as e:
            return {'success': False, 'message': f'导航到URL时出错: {str(e)}'}
    
    def _type_text_step(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """输入文本步骤"""
        text = params.get('text', '')
        if not text:
            return {'success': False, 'message': '未指定文本内容'}
        
        try:
            # 输入文本
            pg.typewrite(text)
            return {'success': True, 'message': f'已输入文本: {text}'}
            
        except Exception as e:
            return {'success': False, 'message': f'输入文本时出错: {str(e)}'}
    
    def _perform_calculation_step(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行计算步骤"""
        expression = params.get('expression', '')
        if not expression:
            return {'success': False, 'message': '未指定计算表达式'}
        
        try:
            # 输入计算表达式
            pg.typewrite(expression)
            time.sleep(1)
            
            # 按等号
            pg.press('enter')
            time.sleep(1)
            
            return {'success': True, 'message': f'已执行计算: {expression}'}
            
        except Exception as e:
            return {'success': False, 'message': f'执行计算时出错: {str(e)}'}
    
    def _find_wechat_login_interface(self) -> bool:
        """查找微信登录界面"""
        try:
            # 查找微信窗口
            wechat_window = ua.FindFirstControl(
                ua.ControlType.WindowControl,
                lambda c: "微信" in c.Name or "WeChat" in c.Name
            )
            return wechat_window is not None
        except:
            return False
    
    def _find_browser_ready(self) -> bool:
        """查找浏览器就绪状态"""
        try:
            # 查找浏览器窗口
            browser_window = ua.FindFirstControl(
                ua.ControlType.WindowControl,
                lambda c: any(browser in c.Name for browser in ["Chrome", "Firefox", "Edge", "Safari"])
            )
            return browser_window is not None
        except:
            return False
    
    def _find_text_editor(self) -> bool:
        """查找文本编辑器"""
        try:
            # 查找记事本窗口
            notepad_window = ua.FindFirstControl(
                ua.ControlType.WindowControl,
                lambda c: "记事本" in c.Name or "Notepad" in c.Name
            )
            return notepad_window is not None
        except:
            return False
    
    def _find_calculator_interface(self) -> bool:
        """查找计算器界面"""
        try:
            # 查找计算器窗口
            calc_window = ua.FindFirstControl(
                ua.ControlType.WindowControl,
                lambda c: "计算器" in c.Name or "Calculator" in c.Name
            )
            return calc_window is not None
        except:
            return False
    
    def add_custom_workflow(self, workflow_name: str, workflow_config: Dict[str, Any]):
        """添加自定义工作流程"""
        self.workflows[workflow_name] = workflow_config
        print(f"✅ 已添加自定义工作流程: {workflow_name}")
    
    def get_available_workflows(self) -> List[str]:
        """获取可用工作流程列表"""
        return list(self.workflows.keys())
    
    def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """获取工作流程信息"""
        return self.workflows.get(workflow_name)

# 测试函数
def test_workflow_manager():
    """测试工作流程管理器"""
    manager = SoftwareWorkflowManager()
    
    print("可用工作流程:")
    for workflow_name in manager.get_available_workflows():
        info = manager.get_workflow_info(workflow_name)
        print(f"- {workflow_name}: {info['name']}")
    
    # 测试记事本工作流程
    print("\n测试记事本工作流程...")
    result = manager.execute_workflow("notepad", {"text": "Hello, World!"})
    print(f"执行结果: {result}")

if __name__ == "__main__":
    test_workflow_manager()
