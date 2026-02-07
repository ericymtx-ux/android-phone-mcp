# GUI 多模态理解模型深度对比

> 调研时间: 2026-02-05

## 一、主流模型性能对比

### ScreenSpot Benchmark 评测结果

| 模型 | 参数量 | Android Text | Android Icon | 平均准确率 | 是否开源 |
|------|--------|--------------|--------------|-----------|---------|
| **SeeClick** | 9.6B | 78.0% | 52.0% | **53.4%** | ✅ 开源 |
| **CogAgent** | 18B | 67.0% | 24.0% | 47.4% | ✅ 开源 |
| **Fuyu** | 8B | 41.0% | 1.3% | 19.5% | ✅ 开源 |
| GPT-4V | - | 22.6% | 24.5% | 16.2% | ❌ API |
| Qwen-VL | 9.6B | 9.5% | 4.8% | 5.2% | ✅ 开源 |
| MiniGPT-v2 | 7B | 8.4% | 6.6% | 5.7% | ✅ 开源 |

**结论**: SeeClick 在 Android UI 理解上表现最佳，推荐作为首选。

---

## 二、模型详细分析

### 2.1 SeeClick (推荐)

**论文**: [SeeClick: Harnessing GUI Grounding for Advanced Visual GUI Agents](https://arxiv.org/abs/2401.10935)

**架构**: 基于 Qwen-VL 微调

**特点**:
- ✅ Android UI 理解准确率最高 (78% Text, 52% Icon)
- ✅ 开源免费，可本地部署
- ✅ 输出归一化坐标 (0-1)，易于转换
- ✅ 支持自定义微调

**安装使用**:
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image

# 加载模型
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen-VL-Chat", 
    trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    "cckevinn/SeeClick",
    device_map="cuda",
    trust_remote_code=True
).eval()

# 预测点击位置
image = Image.open("screenshot.png")
prompt = "In this UI screenshot, what is the position of the element corresponding to the command \"点击搜索\" (with point)?"

query = tokenizer.from_list_format([
    {'image': 'screenshot.png'},
    {'text': prompt},
])

response, _ = model.chat(tokenizer, query=query, history=None)
print(response)  # (0.35, 0.67) 归一化坐标
```

**资源需求**:
- GPU: 至少 24GB VRAM (A10G/4090)
- 内存: 32GB+
- 推理速度: ~1-2秒/图

---

### 2.2 CogAgent (推荐)

**论文**: [CogAgent: A Visual Language Model for GUI Agents](https://arxiv.org/abs/2312.08914)
**版本**: CogAgent-9B-20241220 (最新)

**特点**:
- ✅ 支持高分辨率 (2240x2240)
- ✅ 中英文双语支持
- ✅ 智谱官方产品验证 (GLM-PC)
- ✅ 支持多种动作: click, scroll, type, hotkey
- ✅ 提供在线 Demo

**HuggingFace**: https://huggingface.co/THUDM/cogagent-9b-20241220

**在线体验**:
- HuggingFace Space: https://huggingface.co/spaces/THUDM-HF-SPACE/CogAgent-Demo
- ModelScope: https://modelscope.cn/studios/ZhipuAI/CogAgent-Demo

**本地部署**:
```python
from transformers import CogAgentForCausalLM, AutoTokenizer
from PIL import Image

# 加载模型
tokenizer = AutoTokenizer.from_pretrained("THUDM/cogagent-9b-20241220",
    trust_remote_code=True)
model = CogAgentForCausalLM.from_pretrained(
    "THUDM/cogagent-9b-20241220",
    device_map="auto",
    trust_remote_code=True
).eval()

# 分析截图
image = Image.open("screenshot.png")
instruction = "点击右上角设置按钮"

result = model.predict_action(image, instruction)
print(result)
# {'action': 'click', 'x': 1024, 'y': 512, 'reason': '...'}
```

**资源需求**:
- GPU: 至少 29GB VRAM (A100/H100)
- INT8: ~15GB
- INT4: ~8GB (不推荐，精度损失大)

---

### 2.3 ScreenSpot-Pro (新)

**论文**: [ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use](https://arxiv.org/html/2504.07981v1)

**特点**:
- ✅ 专为高分辨率设计 (4K 显示器)
- ✅ 渐进式区域裁剪策略
- ✅ 2025 最新模型

**适用场景**: 电脑端 GUI 操作 > 手机端

---

### 2.4 API 方案 (快速验证)

#### GPT-4V / Claude Vision

**优点**:
- ✅ 无需 GPU
- ✅ 推理能力强
- ✅ 即开即用

**缺点**:
- ❌ 费用: $0.01-0.06/图
- ❌ 延迟: 2-5秒
- ❌ 数据隐私 (图片上传云端)

**使用示例**:
```python
import base64
import requests
from PIL import Image

def predict_with_gpt4v(image_path: str, instruction: str) -> dict:
    """使用 GPT-4V 预测点击位置"""
    
    # 编码图片
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    prompt = f"""你是一个 UI 助手。
这是一张手机截图。
请根据指令预测应该点击的位置。

指令: {instruction}

请直接输出 JSON 格式，坐标为相对于图片宽高的百分比 (0-1):
{{"action": "click", "x": <x>, "y": <y>, "reason": "原因"}}
"""
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }},
                    {"type": "text", "text": prompt}
                ]
            }]
        }
    )
    
    return parse_response(response.json())
```

---

## 三、成本与性能对比

### 3.1 成本对比

| 方案 | 首次部署成本 | 单次推理成本 | 延迟 |
|------|------------|-------------|------|
| **SeeClick 本地** | ~$2000 (GPU) | $0 | <1s |
| **CogAgent 本地** | ~$2000 (A100) | $0 | 1-2s |
| **GPT-4V API** | $0 | $0.03/图 | 2-3s |
| **Claude Vision** | $0 | $0.03/图 | 2-3s |

### 3.2 推荐选择

| 场景 | 推荐方案 |
|------|----------|
| **快速验证** | GPT-4V API |
| **个人/小团队** | SeeClick + 消费级 GPU (4090) |
| **企业生产** | CogAgent + A100 |
| **离线环境** | SeeClick INT8 |

---

## 四、集成建议

### 4.1 MVP 阶段 (1周)

```
ADB 截图 → GPT-4V API → ADB 执行
```

**优势**: 快速验证，成本低
**劣势**: API 费用，数据隐私

### 4.2 生产阶段 (2-3周)

```
uiautomator2 截图 → SeeClick 本地 → ADB 执行
```

**优势**: 零成本，高性能
**劣势**: 需 GPU 服务器

### 4.3 高级功能

| 功能 | 实现方案 |
|------|----------|
| 滚动 | uiautomator2 scroll() |
| 输入 | uiautomator2 set_text() |
| 长按 | uiautomator2.long_click() |
| 手势 | uiautomator2.drag() |
| OCR | Tesseract / Baidu OCR |
| 控件识别 | uiautomator2 dump_hierarchy |

---

## 五、下一步行动

### Day 1-2: POC
- [ ] ADB 截图测试
- [ ] GPT-4V API 集成
- [ ] 端到端流程验证

### Day 3-4: 本地化
- [ ] 部署 SeeClick / CogAgent
- [ ] 性能优化
- [ ] 批量推理测试

### Day 5-7: 生产化
- [ ] MCP Server 完善
- [ ] 错误处理
- [ ] 集成测试

