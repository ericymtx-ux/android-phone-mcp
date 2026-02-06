# Android Phone MCP Server

通过 USB 调试控制 Android 真机的 MCP Server，集成了火山引擎 (Volcengine) GUI Agent 能力。

## 🌟 核心特性

- **设备控制**: 支持点击、滑动、输入文本、物理按键等基础操作。
- **智能感知**: 提供截图压缩、XML 简化 (Compact XML) 功能，优化 VLM 识别效率。
- **AI 增强**: 内置火山引擎 GUI Agent 集成，支持自然语言指令控制（如"打开微信发消息"）。
- **坐标自适应**: 支持 0-1000 归一化坐标，适配不同分辨率设备。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装系统依赖 (macOS)
brew install android-platform-tools scrcpy
```

### 2. 配置环境变量 (可选)

如果你需要使用火山引擎的 GUI Agent 功能，请设置 API Key：

```bash
export ARK_API_KEY="你的_API_KEY"
```

### 3. 运行 Server

```bash
# 开发模式运行
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/android_phone/server.py
```

## 🛠️ 工具列表

### 基础控制
| 工具 | 参数 | 说明 |
|------|------|------|
| `connect` | serial (可选) | 连接设备 |
| `get_screen_state` | compact_xml, scale | **核心**。获取截图和 UI 树。 |
| `tap` | x, y, normalized | 点击 (支持归一化坐标) |
| `tap_element` | text / resource_id | 智能点击 (根据文本或 ID) |
| `swipe` | x1, y1, x2, y2, normalized | 滑动 |
| `input_text` | text | 输入文本 |
| `press_key` | key | 物理按键 (home, back, etc) |
| `list_apps` | - | 列出第三方应用 |
| `unlock_device` | - | 尝试解锁屏幕 |

### AI Agent 集成
| 工具 | 参数 | 说明 |
|------|------|------|
| `ask_volcengine_agent` | instruction | 发送指令给火山引擎 GUI 模型，获取操作建议 |
| `reset_volcengine_session` | - | 重置多轮对话历史 |

## 📚 开发进度

详见 [开发进度文档](docs/status/roadmap.md)。

## 🧪 测试

```bash
# 运行所有测试
cd tests && python3 -m pytest -v

# 或从项目根目录运行
python3 -m pytest tests/ -v

# 运行连接验证脚本
python3 scripts/verify_device.py
```

### 测试覆盖

| 模块 | 测试文件 | 测试数 | 状态 |
|------|----------|--------|------|
| Parser | test_parser.py | 17 | ✅ 100% |
| Controller | test_controller.py | 2 | ✅ 100% |
| Server | test_server.py | 2 | ✅ 100% |
| **总计** | | **21** | **✅** |

### 火山引擎 Action Parser

解析火山引擎 GUI Agent 返回的动作指令，支持以下格式：

```
Thought: <思考过程>
Action: <动作>(<参数>)
```

**支持的动作用于**:
- `click(point='<point>x y</point>')` - 点击坐标
- `type(content='文本')` - 输入文本
- `swipe(direction='up|down|left|right')` - 滑动
- `drag(start_point='<point>x y</point>', end_point='<point>x y</point>')` - 拖拽
- `hotkey(key='enter')` - 快捷键
- `finished(content='结果')` - 任务完成
```
