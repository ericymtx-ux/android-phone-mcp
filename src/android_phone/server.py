"""Android Phone MCP Server

通过 USB 调试控制 Android 真机，支持 VLM 视觉控制。
依赖: scrcpy (投屏), uiautomator2 (自动化), Pillow (图像处理)
"""

import subprocess
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from android_phone.core.controller import AndroidController
from android_phone.integrations.volcengine import VolcengineGUIClient
from android_phone.core.agent import AutonomousAgent

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP("android-phone-mcp")

# Global Controller & Client
controller = AndroidController()
volcengine_client = VolcengineGUIClient()
agent = AutonomousAgent(controller, volcengine_client)

_scrcpy_process: Optional[subprocess.Popen] = None

@app.tool()
def run_autonomous_task(goal: str, max_steps: int = 50) -> str:
    """
    运行自主任务.
    Agent 会自动: 截图 -> 分析 -> 操作 -> 循环, 直到完成任务.
    
    Args:
        goal: 任务目标 (例如 "打开通达信 app，找到上证指数页面，返回 K 线图").
        max_steps: 最大尝试步数 (默认 50).
    """
    try:
        result = agent.run(goal, max_steps)
        return json.dumps({"status": "ok", "result": result}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@app.tool()
def connect(serial: str = None) -> str:
    """
    连接 Android 设备.
    
    Args:
        serial: 设备序列号 (可选). 如果为空，连接第一个可用设备.
    """
    try:
        if serial:
            controller.serial = serial
        
        controller.connect()
        info = controller.get_info()
        
        return json.dumps({
            "status": "connected",
            "device": info.get("productName", "Unknown"),
            "androidVersion": info.get("sdkInt", "Unknown"),
            "manufacturer": info.get("product", "Unknown"),
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@app.tool()
def get_screen_state(include_xml: bool = False, compact_xml: bool = True, scale: float = 1.0) -> str:
    """
    获取当前屏幕状态 (截图 + 可选 XML).
    Agent 应该在每次操作前调用此工具来观察环境.
    
    Args:
        include_xml: 是否包含 UI 树.
        compact_xml: 是否简化 UI 树 (默认 True).
        scale: 截图缩放比例 (0.1 - 1.0), 默认 1.0. 调小可以节省 Token.
    
    Returns:
        JSON string containing:
        - image: Base64 encoded JPEG image (resized to max 1080p).
        - xml: UI hierarchy XML string (if include_xml is True).
        - info: Device info (width, height, etc).
    """
    try:
        image_b64 = controller.get_screenshot(scale=scale)
        result = {
            "status": "ok",
            "image": image_b64,
            "info": controller.get_info()
        }
        
        if include_xml:
            if compact_xml:
                result["xml"] = controller.get_compact_ui_hierarchy()
            else:
                result["xml"] = controller.get_ui_hierarchy()
            
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@app.tool()
def tap_element(text: str = None, resource_id: str = None) -> str:
    """
    点击 UI 元素 (通过文本或 ID). 比坐标点击更稳定.
    
    Args:
        text: 元素文本 (例如 "微信", "发送").
        resource_id: 元素资源ID (例如 "com.tencent.mm:id/text").
    """
    if controller.click_element(text=text, resource_id=resource_id):
        return json.dumps({"status": "ok", "action": "tap_element", "target": {"text": text, "id": resource_id}}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": "Failed to find or click element"}, ensure_ascii=False)

@app.tool()
def ask_volcengine_agent(instruction: str) -> str:
    """
    将当前屏幕和指令发送给火山引擎 GUI Agent 模型，获取操作建议.
    
    注意: 需要设置 ARK_API_KEY 环境变量.
    
    Args:
        instruction: 你的指令 (例如: "打开微信发送消息").
        
    Returns:
        模型的回复 (JSON). 通常包含对屏幕的分析和建议的下一步动作.
    """
    try:
        # 1. Capture screen
        image_b64 = controller.get_screenshot(quality=60, max_size=(720, 1280)) # Optimize for API
        
        # 2. Call Volcengine API
        response = volcengine_client.ask(instruction, image_b64)
        
        # 3. Return raw response (Agent can parse it)
        return json.dumps({
            "status": "ok",
            "model_response": response
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@app.tool()
def reset_volcengine_session() -> str:
    """
    清空火山引擎 GUI Agent 的多轮对话历史.
    当开始一个新的任务时，建议先调用此工具.
    """
    try:
        volcengine_client.reset_session()
        return json.dumps({"status": "ok", "message": "Session reset successfully"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@app.tool()
def tap(x: int, y: int, normalized: bool = False) -> str:
    """
    点击屏幕坐标.
    
    Args:
        x: X 坐标
        y: Y 坐标
        normalized: 如果为 True, 坐标应为 0-1000 的归一化坐标.
    """
    if normalized:
        x, y = controller.denormalize_coordinates(x, y)
        
    if controller.click(x, y):
        return json.dumps({"status": "ok", "action": "tap", "position": {"x": x, "y": y}}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": "Failed to tap"}, ensure_ascii=False)

@app.tool()
def swipe(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5, normalized: bool = False) -> str:
    """
    滑动屏幕.
    
    Args:
        x1, y1: 起始坐标
        x2, y2: 结束坐标
        duration: 持续时间 (秒)
        normalized: 如果为 True, 坐标应为 0-1000 的归一化坐标.
    """
    if normalized:
        x1, y1 = controller.denormalize_coordinates(x1, y1)
        x2, y2 = controller.denormalize_coordinates(x2, y2)

    if controller.swipe(x1, y1, x2, y2, duration):
        return json.dumps({"status": "ok", "action": "swipe"}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": "Failed to swipe"}, ensure_ascii=False)

@app.tool()
def input_text(text: str, clear: bool = True) -> str:
    """
    输入文本. 确保输入框已获取焦点.
    
    Args:
        text: 要输入的文本
        clear: 是否先清空输入框 (默认 True)
    """
    if controller.input_text(text, clear):
        return json.dumps({"status": "ok", "action": "input", "text": text}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": "Failed to input text"}, ensure_ascii=False)

@app.tool()
def press_key(key: str) -> str:
    """
    按下物理按键.
    
    Args:
        key: home, back, recent, enter, delete, volume_up, volume_down, power
    """
    if controller.press_key(key):
        return json.dumps({"status": "ok", "action": "press_key", "key": key}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": f"Failed to press key {key}"}, ensure_ascii=False)

@app.tool()
def launch_app(package_name: str) -> str:
    """
    启动应用.
    
    Args:
        package_name: 应用包名 (例如 com.tencent.mm)
    """
    if controller.launch_app(package_name):
        return json.dumps({"status": "ok", "action": "launch_app", "package": package_name}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": f"Failed to launch {package_name}"}, ensure_ascii=False)

@app.tool()
def stop_app(package_name: str) -> str:
    """
    停止应用.
    
    Args:
        package_name: 应用包名
    """
    if controller.stop_app(package_name):
        return json.dumps({"status": "ok", "action": "stop_app", "package": package_name}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": f"Failed to stop {package_name}"}, ensure_ascii=False)

@app.tool()
def list_apps() -> str:
    """
    列出已安装的第三方应用包名.
    """
    apps = controller.list_apps()
    return json.dumps({"status": "ok", "apps": apps}, ensure_ascii=False)

@app.tool()
def unlock_device() -> str:
    """
    尝试唤醒并解锁屏幕.
    """
    if controller.unlock_device():
        return json.dumps({"status": "ok", "action": "unlock"}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": "Failed to unlock"}, ensure_ascii=False)

# --- Legacy / Utility Tools ---

@app.tool()
def start_scrcpy() -> str:
    """启动 scrcpy 投屏 (用于人工观察)"""
    global _scrcpy_process
    try:
        result = subprocess.run(["which", "scrcpy"], capture_output=True, text=True)
        if result.returncode != 0:
            return json.dumps({"status": "error", "message": "scrcpy 未安装"}, ensure_ascii=False)
        
        _scrcpy_process = subprocess.Popen(
            ["scrcpy", "--turn-screen-off"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return json.dumps({"status": "ok", "message": "scrcpy started"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@app.tool()
def stop_scrcpy() -> str:
    """停止 scrcpy 投屏"""
    global _scrcpy_process
    try:
        if _scrcpy_process:
            _scrcpy_process.terminate()
            _scrcpy_process = None
        return json.dumps({"status": "ok", "message": "scrcpy stopped"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    app.run()
