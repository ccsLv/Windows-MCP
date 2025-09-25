# 桌面AI助手

基于Windows MCP和Qwen3的智能桌面助手，提供悬浮球界面，可以通过对话操控您的Windows电脑。

## 功能特性

- 🎯 **悬浮球界面**: 简洁的悬浮球设计，双击打开对话窗口
- 🤖 **Qwen3集成**: 使用阿里云通义千问模型进行智能对话
- 🖥️ **桌面操控**: 支持启动应用、执行命令、UI操作等
- 💬 **自然对话**: 支持中文对话，理解用户意图并执行相应操作
- 🎨 **现代UI**: 美观的聊天界面，支持拖拽和自定义样式

## 主要功能

### 桌面操作
- 启动Windows应用程序
- 执行PowerShell命令
- 获取桌面状态和UI元素信息
- 鼠标点击、输入、滚动操作
- 窗口管理（切换、调整大小、移动）

### 系统交互
- 剪贴板操作（复制/粘贴）
- 键盘快捷键执行
- 网页内容抓取
- 文件操作

### AI对话
- 自然语言理解
- 智能任务规划
- 上下文记忆
- 工具调用

## 安装说明

### 1. 环境要求
- Python 3.8+
- Windows 10/11
- 网络连接（用于API调用）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥
编辑 `config.json` 文件，设置您的API密钥：
```json
{
    "api_key": "您的API密钥",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-plus"
}
```

## 使用方法

### 启动助手
```bash
python run_assistant.py
```

### 基本操作
1. **启动**: 运行后会在桌面右下角显示悬浮球
2. **打开对话**: 双击悬浮球打开聊天窗口
3. **移动位置**: 拖拽悬浮球到任意位置
4. **开始对话**: 在聊天窗口中输入您的需求

### 示例对话
- "帮我打开记事本"
- "执行命令查看当前目录文件"
- "点击屏幕上的某个按钮"
- "帮我搜索网页内容"
- "调整窗口大小"

## 配置选项

在 `config.json` 中可以自定义以下选项：

### API配置
- `api_key`: 阿里云API密钥
- `base_url`: API基础URL
- `model`: 使用的模型名称

### UI配置
- `window_width/height`: 聊天窗口大小
- `ball_size`: 悬浮球大小
- `ball_color`: 悬浮球颜色
- `font_family/size`: 字体设置

## 技术架构

### 核心组件
- **FloatingBall**: 悬浮球界面管理
- **Qwen3Client**: AI模型客户端
- **Desktop**: Windows桌面操作接口
- **Config**: 配置管理

### 工具集成
- 启动应用工具
- PowerShell执行工具
- 桌面状态获取工具
- UI元素操作工具
- 剪贴板工具
- 窗口管理工具
- 键盘快捷键工具
- 网页抓取工具

## 故障排除

### 常见问题

1. **悬浮球不显示**
   - 检查Python环境是否正确
   - 确认tkinter模块已安装
   - 检查是否有杀毒软件拦截

2. **AI响应错误**
   - 验证API密钥是否正确
   - 检查网络连接
   - 确认API配额是否充足

3. **桌面操作失败**
   - 确认以管理员权限运行
   - 检查Windows版本兼容性
   - 验证依赖包版本

### 调试模式
在代码中添加调试信息：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 开发说明

### 项目结构
```
├── desktop_assistant.py    # 主程序文件
├── run_assistant.py       # 启动脚本
├── config.json           # 配置文件
├── requirements.txt      # 依赖列表
└── README_Assistant.md   # 说明文档
```

### 扩展功能
要添加新功能，可以：
1. 在 `Qwen3Client._get_tools()` 中添加新工具定义
2. 在 `Qwen3Client._execute_tools()` 中实现工具逻辑
3. 更新配置文件添加新选项

## 许可证

MIT License - 详见 LICENSE.md

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持悬浮球界面
- 集成Qwen3模型
- 实现基础桌面操作功能
