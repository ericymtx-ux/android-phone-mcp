# Android Phone MCP 架构设计文档

> 版本: v0.1
> 日期: 2026-02-05
> 状态: Draft

## 1. 设计目标

构建一个健壮的 Android 设备控制层 (Data Layer) 和 代理交互层 (Agent Layer)，使 AI Agent (如 Claude, OpenClaw, 或 Volcengine GUI Agent) 能够通过 MCP 协议高效、准确地控制 Android 设备。

## 2. 架构概览

```mermaid
graph TD
    User[用户/AI Agent] <--> MCPServer[MCP Server (android-phone-mcp)]
    
    subgraph "Agent Layer (交互层)"
        MCPServer <--> Tool_Observation[观察工具 (Screenshot/XML)]
        MCPServer <--> Tool_Action[执行工具 (Click/Swipe/Type)]
        MCPServer <--> Tool_System[系统工具 (Connect/App)]
    end
    
    subgraph "Data Layer (数据层)"
        Tool_Observation --> DeviceManager[设备管理器]
        Tool_Action --> DeviceManager
        Tool_System --> DeviceManager
        
        DeviceManager <--> U2[uiautomator2]
        DeviceManager <--> ADB[Android Debug Bridge]
    end
    
    subgraph "Device (物理/模拟)"
        U2 <--> AndroidOS[Android OS]
        ADB <--> AndroidOS
    end
```

## 3. Data Layer (数据层) 设计

数据层负责与 Android 设备进行底层通信，屏蔽 ADB 和 uiautomator2 的细节，提供稳定、统一的 Python API。

### 3.1 核心类: `AndroidController`

位置: `src/android_phone/core/controller.py`

此类封装所有设备操作，具备以下特性：
- **单例/多例管理**: 支持管理多个设备。
- **自动重连**: 当设备断开连接时自动尝试重连。
- **异常处理**: 捕获底层库异常，转换为易读的错误信息。
- **性能优化**: 缓存 XML 树，压缩截图。

#### 接口定义 (Draft)

```python
class AndroidController:
    def __init__(self, serial: str = None):
        self.serial = serial
        self.device = None # uiautomator2 device object

    def connect(self) -> bool:
        """连接设备，安装必要的守护进程"""
        pass

    def get_screenshot(self, format="base64", quality=70, max_size=(1080, 1920)) -> str:
        """获取压缩后的截图，适合 VLM 输入"""
        pass

    def get_ui_hierarchy(self, compressed=True) -> str:
        """获取 UI 树 (XML)，可选压缩模式(移除冗余属性)"""
        pass

    def click(self, x: int, y: int) -> bool:
        """坐标点击"""
        pass
    
    def click_element(self, selector: str) -> bool:
        """基于 UI 选择器点击 (比坐标更准)"""
        pass

    def swipe(self, start: tuple, end: tuple, duration: float) -> bool:
        """滑动"""
        pass

    def input_text(self, text: str, clear=True) -> bool:
        """输入文本 (支持 ADB 键盘和广播)"""
        pass
        
    def app_launch(self, package_name: str) -> bool:
        """启动应用"""
        pass
        
    def app_stop(self, package_name: str) -> bool:
        """停止应用"""
        pass
```

### 3.2 优化策略

1.  **截图优化**:
    - VLM 通常不需要原始分辨率 (如 2K/4K)。
    - **策略**: 默认将截图 Resize 到长边 1080px 或 720px，并使用 JPEG 格式 (quality=70) 压缩，大幅减少 Base64 字符串长度 (Token 消耗)。

2.  **XML 优化**:
    - 原始 `dump_hierarchy` 包含大量无关信息 (resource-id, bounds, content-desc, class 等之外的属性)。
    - **策略**: 解析 XML，移除无用节点 (不可见、无交互属性的布局容器)，仅保留叶子节点或关键容器，减少 Context 占用。

## 4. Agent Layer (代理层) 设计

代理层通过 MCP 协议将 Data Layer 的能力暴露给 AI。

### 4.1 MCP Tools 设计

我们将工具分为三类：**观察 (Observation)**、**操作 (Action)**、**元数据 (Meta)**。

#### A. 观察工具 (Observation)

| 工具名 | 参数 | 返回值 | 描述 |
| :--- | :--- | :--- | :--- |
| `get_screen_state` | `include_xml: bool` (default False) | `{"image": "base64...", "xml": "..."}` | **核心工具**。获取当前屏幕状态。Agent 每次操作前应调用此工具。 |
| `get_element_info` | `text` or `resource_id` | `{"bounds": [x,y,w,h], ...}` | 查询特定控件的位置信息 (用于辅助 VLM 定位)。 |

#### B. 操作工具 (Action)

| 工具名 | 参数 | 描述 |
| :--- | :--- | :--- |
| `tap` | `x`, `y` | 点击坐标 (VLM 常用)。 |
| `tap_element` | `selector` (text/id) | 点击控件 (传统 Agent 常用)。 |
| `swipe` | `x1`, `y1`, `x2`, `y2`, `duration` | 滑动屏幕。 |
| `type_text` | `text`, `submit` (bool) | 输入文本，可选是否按回车。 |
| `press_key` | `key` (home, back, recent, enter...) | 物理按键。 |
| `launch_app` | `app_name` (模糊匹配) | 启动 App (需维护 App 名到包名的映射或使用 Launcher 搜索)。 |

#### C. 元数据工具 (Meta)

| 工具名 | 参数 | 描述 |
| :--- | :--- | :--- |
| `list_apps` | None | 列出已安装的第三方应用。 |
| `device_info` | None | 获取屏幕分辨率、系统版本等。 |

### 4.2 Prompt Engineering (提示词策略)

为了让通用 VLM (如 Claude 3.5 Sonnet, GPT-4o) 更好地控制手机，我们需要在 System Prompt 或 Tool Description 中注入 "Android 知识"。

**System Prompt 建议:**
> 你是一个 Android 手机操作助手。你通过 `get_screen_state` 获取屏幕画面。
> 画面中的坐标系原点 (0,0) 在左上角。
> 如果你需要点击某个图标，请先观察截图，估算其中心点坐标 (x, y)，然后调用 `tap(x, y)`。
> 对于文本输入，请确保先点击输入框获取焦点，再调用 `type_text`。
> 遇到不确定的界面，可以先 `swipe` 滑动查看更多内容。

### 4.3 与火山引擎 GUI API 的整合

如果用户配置了 `ARK_API_KEY`，我们可以提供一个**高级工具**，直接利用火山引擎的专用模型。

| 工具名 | 参数 | 描述 |
| :--- | :--- | :--- |
| `ask_volcengine_gui` | `instruction` (e.g. "打开微信给妈妈发消息") | `{"thought": "...", "action": "click(100,200)"}` | 将当前截图和指令发送给火山引擎 GUI 模型，直接获取下一步动作建议。 |

这种方式相当于 "Agent 调用 Agent" (Tool Use)，可以作为本地策略失效时的兜底，或者处理复杂语义理解的场景。

## 5. 开发计划

1.  **Refactor**: 创建 `src/android_phone/core/`，实现 `AndroidController` 类，迁移 `server.py` 中的逻辑。(Done)
2.  **Enhance**: 实现截图压缩和 XML 简化功能。(Done)
    - `get_compact_ui_hierarchy` 已实现，过滤无用节点和属性。
    - `click_element` 已实现，支持文本和 ID 定位。
3.  **MCP Update**: 更新 `server.py`，使用新的 Controller，并对齐上述 Tool 设计。(Done)
    - 新增 `tap_element` 工具。
    - `get_screen_state` 支持 `compact_xml` 参数。
4.  **Integration**: 添加 `volcengine` 集成 (可选，作为独立工具)。(Done)
    - 已集成 Volcengine GUI API，提供 `ask_volcengine_agent` 工具。

## 6. 测试策略

### 6.1 单元测试 (Unit Tests)
验证核心逻辑，不依赖设备。
- 运行: `python3 tests/test_controller.py`
- 覆盖: 
    - XML 简化与过滤逻辑。
    - 坐标归一化/反归一化算法。

### 6.2 集成测试 (Integration Tests)
验证与真机/模拟器的交互。
- 准备: 连接 Android 设备并开启 USB 调试。
- 运行: 
    1. 启动 MCP Inspector 或手动运行验证脚本。
    2. 验证截图获取 (生成文件检查)。
    3. 验证点击/滑动操作 (观察屏幕反应)。
- 脚本: `scripts/verify_device.py` (Planned)

