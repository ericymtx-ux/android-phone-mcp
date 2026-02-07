# Android Autonomous Agent Skill 文档

## 简介
`android-autonomous-agent` 是一个基于视觉推理的自主 Android 代理 Skill。它利用火山引擎（Volcengine）的视觉模型来分析手机屏幕截图，自主规划并执行点击、滑动、输入等操作，从而完成用户下达的复杂指令。

## 目录结构
按照 Claude Code Skills 标准，该 Skill 的文件结构如下：

```
projects/android-phone-mcp/
└── .claude/
    └── skills/
        └── android-autonomous-agent/
            └── SKILL.md  # 核心定义文件 (包含 Frontmatter 配置)
```

## 功能特点
- **视觉导航**：不依赖应用内部 API，像人类一样通过识别图标、文字和布局来操作。
- **自主闭环**：具备“观察-思考-行动”的自主循环能力，能根据操作反馈自动纠错。
- **自然语言交互**：直接听懂“打开微信发消息”、“去通达信看股票”等高层指令。
- **随机等待**：模拟人类操作习惯，操作间隙随机等待 1-3 秒，提高稳定性。

## 安装与配置

1.  **环境依赖**：
    *   确保已安装 `android-phone-mcp` 项目依赖。
    *   Android 手机已通过 USB 连接并开启调试模式 (`adb devices` 可见)。
    *   项目根目录 `.env` 文件中已配置 `ARK_API_KEY`。

2.  **Skill 部署**：
    *   该 Skill 位于项目内的 `.claude/skills/android-autonomous-agent/` 目录，OpenClaw/Claude Code 会自动发现并加载它。

## 使用方法

### 直接调用
在对话框中输入 `/android-autonomous-agent` 加上你的指令：

```bash
/android-autonomous-agent "打开设置，找到显示选项，把亮度调到最大"
```

### 自然对话
你也可以直接在对话中描述需求，Agent 会自动识别并调用此 Skill：

> "帮我看看手机上现在的天气是多少度"
> "打开通达信，帮我找一下贵州茅台的 K 线图"

## 参数说明
*   `goal`: 任务目标描述（必填）。
*   `max_steps`: 最大尝试步数（选填，默认 50 步）。

## 开发与调试
*   Skill 的核心逻辑实现在 `src/android_phone/core/agent.py`。
*   MCP 工具定义在 `src/android_phone/server.py`。
*   可以通过查看控制台日志来监控 Agent 的思考过程（Thought）和执行动作（Action）。
