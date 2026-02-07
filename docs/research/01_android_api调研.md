# 安卓设备控制 API 深度调研

> 调研时间: 2026-02-05

## 一、核心技术栈总览

```
┌─────────────────────────────────────────────────────────────┐
│                    用户需求层                               │
│  "获取截图 → VLM理解 → 生成操作 → 执行操作"                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  VLM 多模态理解层                            │
│  ScreenSpot · UI2 · CogAgent · Qwen-VL · GPT-4V            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  设备控制 API 层                            │
│  ADB           uiautomator2        scrcpy        Appium    │
│  shell         accessibilty         mirror        REST     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   物理设备层                                 │
│  Android 真机 · Android 模拟器                               │
└─────────────────────────────────────────────────────────────┘
```

## 二、安卓设备控制 API 详解

### 2.1 ADB (Android Debug Bridge)

**定位**: 系统级调试桥梁，所有安卓设备控制的根基

**核心能力**:
| 能力 | 命令 | 说明 |
|------|------|------|
| 截图 | `adb exec-out screencap -p /sdcard/screen.png && adb pull /sdcard/screen.png` | 需 root 或可写路径 |
| 点击 | `adb shell input tap x y` | 坐标点击 |
| 滑动 | `adb shell input swipe x1 y1 x2 y2` | 滑动 |
| 输入 | `adb shell input text "hello"` | 文本输入 |
| 按键 | `adb shell input keyevent KEYCODE_HOME` | 系统按键 |
| 截图(新) | `adb shell dumpsys window` | 获取界面层级 |

**截图优化方案**:
```bash
# 方法1: 传统方式 (慢，有黑屏)
adb exec-out screencap -p > screen.png

# 方法2: Framebuffer (需 root)
adb shell "cat /dev/graphics/fb0" > fb0.raw

# 方法3: minicap (推荐，性能最优)
adb shell LD_LIBRARY_PATH=/data/local/tmp/minicap \
  /data/local/tmp/minicap -P 1080x1920@1080x1920/0 -s > screen.png
```

### 2.2 uiautomator2

**定位**: Android UI 自动化的官方框架

**安装**:
```bash
pip install uiautomator2
python -m uiautomator2 init
```

**核心 API**:
```python
import uiautomator2 as u2

d = u2.connect('device_serial')

# 截图 (无损，比 ADB 快)
d.screenshot('/tmp/screen.png')

# 点击 (支持多种方式)
d.click(x, y)              # 坐标
d.click(resourceId="com.app:id/btn")  # 控件
d(text="确定").click()      # 文本定位

# 滑动
d.swipe(x1, y1, x2, y2, duration=0.5)

# 控件操作
d(resourceId="com.app:id/list").child(text="设置").click()

# 等待
d.wait_activity('com.app.MainActivity', timeout=10)
```

**优势**:
- ✅ 官方支持，稳定
- ✅ 控件定位，无需坐标
- ✅ 支持手势
- ✅ Python 原生

**劣势**:
- ❌ 需开启无障碍服务
- ❌ 某些系统页面无法获取 (WebView, OpenGL)

### 2.3 scrcpy

**定位**: 高性能投屏 + 控制，跨平台

**安装**:
```bash
brew install scrcpy
```

**核心能力**:
```bash
# 投屏
scrcpy --serial device_id

# 投屏 + 录制
scrcpy --serial device_id --record file.mp4

# 仅控制
scrcpy --no-video --serial device_id

# 最大码率 (优化低带宽)
scrcpy --serial device_id --max-size 1920 --bit-rate 8M

# 屏幕关闭
scrcpy --turn-screen-off --serial device_id
```

**Python 集成**:
```python
import subprocess

# 启动 scrcpy
proc = subprocess.Popen(['scrcpy', '--serial', device_id, 
                         '--max-size', '1920', '--bit-rate', '8M'])

# 获取截图 (需额外方案)
# scrcpy 不直接提供截图 API，需用 ADB 配合
```

### 2.4 Appium

**定位**: 企业级移动自动化框架

**架构**:
```
┌─────────────────────────────────────────┐
│          Appium Server                  │
│    (Java, Node.js, Python)              │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌───────┐  ┌──────────┐  ┌──────────┐
│ADB    │  │XCUITest  │  │UIAutomator│
│Android│  │iOS       │  │Android   │
└───────┘  └──────────┘  └──────────┘
```

**适用场景**:
- ✅ 企业应用测试
- ✅ 跨平台 (iOS + Android)
- ✅ CI/CD 集成
- ❌ 重量级，启动慢
- ❌ 学习曲线陡

## 三、多模态 GUI 理解模型

### 3.1 主流模型对比

| 模型 | 机构 | 特点 | 手机端支持 |
|------|------|------|-----------|
| **ScreenSpot** | UIUC | 专注 UI 交互点预测 | ✅ |
| **UI2** | 字节 | UI 理解 + 生成 | ✅ |
| **CogAgent** | 智谱 | GUI 代理 + 操作 | ✅ |
| **Qwen-VL** | 阿里 | 开源，支持长文本 | ✅ |
| **GPT-4V** | OpenAI | 通用多模态 | API |
| **Claude Vision** | Anthropic | 强大推理 | API |

### 3.2 ScreenSpot (推荐)

**论文**: "ScreenSpot: Can Large Language Models Correctly 
Locate UI Elements?"

**能力**:
- 输入: 截图 + 指令 ("点击搜索按钮")
- 输出: (x, y) 坐标

**使用方式**:
```python
from PIL import Image
import base64

# 本地部署 (需 GPU)
from screen_spot import ScreenSpotModel

model = ScreenSpotModel.load('checkpoint.pt')

image = Image.open('screenshot.png')
instruction = "点击右上角设置"
coords = model.predict(image, instruction)

print(f"预测坐标: {coords}")  # (x, y)
```

**API 服务**:
```bash
# 启动服务
python -m screen_spot serve --port 8080

# 调用
curl -X POST http://localhost:8080/predict \
  -F "image=@screen.png" \
  -F "instruction=点击搜索"
```

### 3.3 UI2 (字节跳动手臂)

**定位**: 端到端 UI 自动化代理

**能力**:
- UI 理解: 识别按钮、输入框、列表
- 操作生成: 预测点击、滑动、输入
- 任务规划: 完成复杂多步操作

**集成方式**:
```python
from ui2 import UI2Agent

agent = UI2Agent(model='qwen-vl')

# 执行任务
task = "打开同花顺，点击自选股，查看第一个股票"
result = agent.run(task)

print(result)  # {'success': True, 'actions': [...], 'screenshot': '...'}
```

### 3.4 CogAgent (智谱)

**论文**: "CogAgent: A Visual Agent for GUI Tasks"

**特点**:
- 高分辨率图像理解 (2240x2240)
- 精准 UI 元素定位
- 支持 90+ 种语言

**使用**:
```python
from cogagent import CogAgent

agent = CogAgent()

# 分析截图
analysis = agent.analyze(
    image='screenshot.png',
    task='找到并点击"确认"按钮'
)
print(analysis.predicted_action)  # {'type': 'click', 'x': 256, 'y': 512}
```

## 四、完整技术链路设计

### 4.1 推荐架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Android Phone MCP Server                      │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ 设备连接 │───►│  截图获取    │───►│  VLM 理解服务        │   │
│  │ uiautom2 │    │ (uiautomator2)│   │ (ScreenSpot/Qwen-VL) │   │
│  └──────────┘    └──────────────┘    └──────────┬───────────┘   │
│                                                   │               │
│                                                   ▼               │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ 执行操作 │◄───│  操作映射    │◄───│  指令生成            │   │
│  │ (ADB)    │    │ (坐标→动作)  │    │ (自然语言)           │   │
│  └──────────┘    └──────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 MCP Tool 设计

```python
# android_phone_mcp/tools.py

from mcp.server import Tool

TOOLS = [
    Tool(
        name="connect_device",
        description="连接 Android 设备 (USB 调试)",
        params={
            "serial": {"type": "string", "description": "设备序列号"}
        },
        handler=connect_device
    ),
    
    Tool(
        name="analyze_and_click",
        description="分析截图并执行点击操作",
        params={
            "instruction": {"type": "string", "description": "操作指令，如 '点击搜索按钮'"},
            "screenshot_path": {"type": "string", "description": "截图路径 (可选，自动截取)"}
        },
        handler=analyze_and_click
    ),
    
    Tool(
        name="execute_task",
        description="执行复杂多步任务",
        params={
            "task": {"type": "string", "description": "任务描述，如 '打开同花顺自选股'"},
            "max_steps": {"type": "integer", "default": 10, "description": "最大步数"}
        },
        handler=execute_task
    ),
]
```

### 4.3 VLM 集成代码示例

```python
# vlm_client.py
import base64
import requests
from PIL import Image

class GUIVLMClient:
    """GUI 理解 VLM 客户端"""
    
    def __init__(self, provider="screen_spot"):
        self.provider = provider
        self.endpoint = "http://localhost:8080"  # VLM 服务地址
        
    def predict_click(self, image_path: str, instruction: str) -> dict:
        """预测点击坐标"""
        
        if self.provider == "screen_spot":
            return self._screen_spot_predict(image_path, instruction)
        elif self.provider == "qwen_vl":
            return self._qwen_vl_predict(image_path, instruction)
            
    def _screen_spot_predict(self, image_path: str, instruction: str) -> dict:
        """ScreenSpot 预测"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'instruction': instruction}
            response = requests.post(
                f"{self.endpoint}/predict",
                files=files,
                data=data
            )
            return response.json()
    
    def _qwen_vl_predict(self, image_path: str, instruction: str) -> dict:
        """Qwen-VL 预测 (带推理)"""
        
        prompt = f"""你是一个 UI 助手。
截图中是一个手机屏幕。
请根据指令预测操作坐标。

指令: {instruction}

请直接输出 JSON 格式:
{{"action": "click", "x": <x坐标>, "y": <y坐标>, "reason": "原因"}}
"""
        
        # 编码图片
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode()
        
        # 调用 API
        response = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "MiniMax-VL-Think",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            }
        )
        
        return self._parse_response(response.json())
```

## 五、备选方案评估

### 5.1 纯 API 方案 (低成本)

```
ADB + GPT-4V API
├── 截图: adb exec-out screencap
├── 理解: GPT-4V API ($0.01/图)
└── 执行: adb shell input tap
```

**成本**: $0.01/次操作
**延迟**: 2-5 秒
**推荐**: ✅ MVP 验证

### 5.2 本地模型方案 (高性能)

```
minicap + Qwen-VL 本地
├── 截图: minicap (60fps)
├── 理解: Qwen-VL-7B (本地 GPU)
└── 执行: adb shell input tap
```

**成本**: 一次性硬件投入
**延迟**: <1 秒
**推荐**: ✅ 生产环境

### 5.3 混合方案 (推荐)

```
按需选择:
├── 简单操作: uiautomator2 控件定位 (免费)
├── 复杂操作: VLM 坐标预测 (付费)
└── 兜底: ADB 指令 (通用)
```

## 六、下一步行动

### 6.1 POC 验证 (1-2 天)

- [ ] ADB 截图测试
- [ ] GPT-4V API 集成
- [ ] 端到端流程跑通

### 6.2 本地化部署 (3-5 天)

- [ ] 部署 ScreenSpot/Qwen-VL 本地
- [ ] 性能优化 (批量推理)
- [ ] 延迟测试 < 2s

### 6.3 生产化 (1 周)

- [ ] MCP Server 完善
- [ ] 错误处理 + 重试
- [ ] 集成测试

