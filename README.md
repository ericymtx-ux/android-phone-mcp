# Android Phone MCP Server

通过 USB 调试控制 Android 真机的 MCP Server。

## 安装

```bash
# 安装依赖
pip install mcp uiautomator2

# 安装 scrcpy (macOS)
brew install scrcpy android-platform-tools
```

## 使用

### 方式 1: 直接运行

```bash
cd src
python -m android_phone.server
```

### 方式 2: MCP CLI

```bash
mcp run-android-phone
```

## 可用工具

| 工具 | 参数 | 说明 |
|------|------|------|
| connect | - | 连接 Android 设备 |
| disconnect | - | 断开连接 |
| click | x, y | 点击坐标 |
| swipe | x1, y1, x2, y2, duration | 滑动 |
| input_text | text | 输入文本 |
| press | key | 按键 (home/back/menu/power) |
| screenshot | path | 截图 |
| get_info | - | 获取设备信息 |
| start_scrcpy | - | 启动投屏 |
| stop_scrcpy | - | 停止投屏 |

## 示例

```python
# 连接设备
connect()

# 点击 (100, 200)
click(x=100, y=200)

# 滑动
swipe(x1=100, y1=500, x2=100, y2=100)

# 输入文本
input_text("hello")

# 截图
screenshot("/tmp/screen.png")
```

## 前置条件

1. Android 手机开启 USB 调试
2. 连接 Type-C 数据线到 Mac mini
3. 允许 USB 调试授权

## OpenClaw 集成

在 OpenClaw 中使用 `/android-phone` 命令调用。
