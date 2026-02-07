# 火山引擎 GUI 任务处理 API 调研

> 调研时间: 2026-02-05
> 文档来源: https://www.volcengine.com/docs/82379/1584296

---

## 一、概述

火山引擎 (Volcano Engine) 提供**方舟大模型服务平台**，其中包含 GUI 任务处理能力。

### 核心能力

```
┌─────────────────────────────────────────────────────────┐
│              火山引擎 GUI Agent                          │
│                                                          │
│  截图输入 ──► VLM 理解 ──► 操作指令生成 ──► 执行反馈   │
│     │            │              │              │       │
│  Base64      视觉理解        结构化动作        结果     │
│  图片                                      确认       │
└─────────────────────────────────────────────────────────┘
```

### 适用场景

- ✅ 电脑控制 (Computer Use)
- ✅ 移动设备控制 (Mobile Use)
- ✅ Web 自动化
- ✅ 跨平台操作

---

## 二、API 调用方式

### 2.1 安装 SDK

```bash
pip install volcengine-python-sdk[ark]
```

### 2.2 基础调用示例

```python
import os
from volcenginesdkarkruntime import Ark
import base64

# 初始化 Ark 客户端
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
)

# 图片转 Base64
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# 调用 GUI 任务处理
response = client.chat.completions.create(
    model="GUI-Model-ID",  # 具体模型 ID 需查看控制台
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encode_image('screenshot.png')}"
                    }
                },
                {
                    "type": "text",
                    "text": "Could you help me set the image to Palette-Based?"
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

### 2.3 系统提示模板

火山引擎提供预定义的提示词模板 (`COMPUTER_USE_DOUBAO` 等)，用于指定任务与语言。

```python
from prompt import COMPUTER_USE_DOUBAO

instruction = "打开设置，点击WiFi"
```

---

## 三、GUI Agent 框架对比 (火山文档)

根据火山引擎技术文档，主流 GUI Agent 框架:

### 3.1 移动端 Agent

| 框架 | 特点 | 技术栈 |
|------|------|--------|
| **AppAgent** | 自主探索学习新应用 | GPT-4V + XML |
| **AppAgent-V2** | 增强视觉识别 + 安全检查 | GPT-4V + 结构化数据 |
| **Mobile-Agent** | OCR/CLIP/Grounding DINO | 多视觉工具 |
| **Mobile-Agent-v2** | 多Agent架构 | Qwen-VL-Int4 |
| **VisionTasker** | 视觉解析 + 任务规划 | YOLO-v8 + PaddleOCR |
| **CoCo-Agent** | 综合事件感知 | Android in the Wild 数据 |
| **MobileGPT** | 模拟人类认知过程 | 分层记忆结构 |

### 3.2 电脑端 Agent

| 框架 | 特点 | 平台 |
|------|------|------|
| **UFO** | 双Agent架构 (HostAgent + AppAgent) | Windows |
| **Cradle** | 六模块结构 (信息收集 + 自我反思) | 跨软件 |
| **OS-Copilot** | 通用框架 | Linux/macOS |

### 3.3 跨平台 Agent

| 框架 | 特点 |
|------|------|
| **AutoGLM** | 中间接口设计，网页+Android |
| **TinyClick** | 轻量级 (0.27亿参数) |
| **OSCAR** | 状态机架构 |

---

## 四、集成方案设计

### 4.1 火山引擎集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Android Phone MCP Server                      │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ 设备连接 │───►│  截图获取    │───►│  火山引擎 API       │   │
│  │ uiautom2 │    │ Base64 编码  │    │ GUI 任务处理        │   │
│  └──────────┘    └──────────────┘    └──────────┬───────────┘   │
│                                                   │               │
│                                                   ▼               │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ 执行操作 │◄───│  动作解析    │◄───│  操作指令响应      │   │
│  │ ADB      │    │ 坐标提取     │    │ click/swipe/input   │   │
│  └──────────┘    └──────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 MCP Tool 设计

```python
TOOLS = [
    Tool(
        name="volcano_gui_task",
        description="使用火山引擎 GUI 任务处理",
        params={
            "instruction": {"type": "string", "description": "操作指令"},
            "screenshot_path": {"type": "string", "description": "截图路径"}
        },
        handler=volcano_gui_task
    ),
]
```

### 4.3 代码示例

```python
# volcano_gui_client.py

import os
import base64
from volcenginesdkarkruntime import Ark

class VolcanoGUIClient:
    """火山引擎 GUI 任务处理客户端"""
    
    def __init__(self, api_key: str = None):
        self.client = Ark(api_key=api_key or os.getenv('ARK_API_KEY'))
        self.model = "volcengine-gui-model"  # 需确认具体模型 ID
        
    def encode_image(self, image_path: str) -> str:
        """图片转 Base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def execute_task(self, screenshot_path: str, instruction: str) -> dict:
        """执行 GUI 任务"""
        
        # 编码图片
        image_base64 = self.encode_image(screenshot_path)
        
        # 调用 API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    },
                    {
                        "type": "text",
                        "text": instruction
                    }
                ]
            }]
        )
        
        # 解析响应
        result = response.choices[0].message.content
        return self._parse_action(result)
    
    def _parse_action(self, response: str) -> dict:
        """解析操作指令"""
        # 火山引擎返回格式示例:
        # {"action": "click", "x": 256, "y": 512, "reason": "点击设置按钮"}
        
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON
            import re
            match = re.search(r'\{[^}]+\}', response)
            if match:
                return json.loads(match.group())
            raise ValueError(f"无法解析响应: {response}")
```

---

## 五、模型选择建议

### 5.1 火山引擎可选方案

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **火山方舟 GUI** | 官方支持，集成简单 | 需 API Key | 快速验证 |
| **自托管 SeeClick** | 开源免费 | 需 GPU | 生产环境 |
| **GPT-4V API** | 成熟稳定 | 费用高 | POC |

### 5.2 推荐策略

```
POC 阶段: 火山方舟 GUI API
    ↓ 验证成功
生产阶段: SeeClick 本地部署 (成本更低)
    ↓ GPU 不足
兜底方案: GPT-4V API
```

---

## 六、已知限制

1. **文档访问**: 火山引擎方舟平台文档需要登录
2. **模型 ID**: 具体模型 ID 需登录控制台查看
3. **API Key**: 需申请火山引擎账号并获取 API Key

---

## 七、相关资源

- 火山方舟平台: https://www.volcengine.com/product/ark
- GUI 任务处理文档: https://www.volcengine.com/docs/82379/1584296
- 多模态理解: https://www.volcengine.com/docs/82379/1958521
- 火山开发者社区: https://developer.volcengine.com/

