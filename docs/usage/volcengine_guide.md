# 火山引擎 GUI Agent 使用指南

Android Phone MCP 内置了对火山引擎 (Volcengine) GUI Agent 的深度集成。这意味着你不需要自己编写复杂的 VLM 逻辑，可以直接利用火山引擎的专用模型（`doubao-seed-1-6-vision`）来控制 Android 手机。

## 1. 原理

该功能实际上实现了 "Agent 调用 Agent" 的模式：

1.  **用户** 向 MCP 发送指令（如 "打开微信"）。
2.  **MCP Server** 截取当前手机屏幕，将截图和指令发送给 **火山引擎 API**。
3.  **火山引擎模型** 分析截图，生成下一步的具体操作（如 `click(500, 1000)`）。
4.  **MCP Server** 解析模型返回的操作，并返回给调用者（或者未来直接执行）。

## 2. 配置

在使用前，必须设置 API Key：

```bash
export ARK_API_KEY="你的火山引擎_API_KEY"
```

## 3. 工具介绍

### `ask_volcengine_agent`

这是核心交互工具。

*   **输入**: `instruction` (字符串)，例如 "点击搜索框输入 OpenClaw"。
*   **行为**:
    1.  自动截取当前屏幕（缩放以适应 API 限制）。
    2.  调用 API，附带历史对话上下文。
    3.  自动维护多轮对话历史（最多保留 5 张截图）。
*   **输出**: JSON 格式，包含模型的思维链 (Thought) 和结构化动作 (Action)。

**示例响应**:
```json
{
  "status": "ok",
  "model_response": {
    "thought": "我看到主屏幕上有微信图标，位于右下角。",
    "action_parsed": {
      "type": "click",
      "x": 800,
      "y": 1600
    },
    "raw_content": "Thought: ... Action: click(point='<point>800 1600</point>')"
  }
}
```

### `reset_volcengine_session`

用于重置多轮对话历史。

*   **使用场景**: 当你想要开始一个全新的任务（例如从 "刷抖音" 切换到 "查邮件"）时，调用此工具可以避免模型被之前的上下文干扰，同时节省 Token。

## 4. 最佳实践 (Prompting)

当你使用 Claude 或其他上层 Agent 来调用此工具时，可以使用以下 Prompt 策略：

> "你是一个手机助手。请循环执行以下步骤来完成我的任务：
> 1. 调用 `ask_volcengine_agent` 获取下一步操作建议。
> 2. 解析返回的 `action_parsed`。
> 3. 如果是 `click` 操作，调用 `tap(x, y, normalized=True)` 执行。
> 4. 如果是 `type` 操作，调用 `input_text` 执行。
> 5. 如果模型说 `finished`，则任务结束。"

## 5. 限制

*   **历史记录**: 为了符合 API 限制，历史记录中最多保留 **5 张** 截图。更早的截图会被自动移除，只保留文本指令。
*   **坐标系**: 火山引擎模型默认输出 **1000x1000** 的归一化坐标。因此，执行时请务必使用 `tap(..., normalized=True)`。
