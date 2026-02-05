"""Android Phone MCP Server

通过 USB 调试控制 Android 真机。
依赖: scrcpy (投屏), uiautomator2 (自动化)
"""

import subprocess
import asyncio
import json
import os
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

app = FastMCP("android-phone-mcp")

# 全局设备引用
_device: Optional[Any] = None
_scrcpy_process: Optional[Any] = None


def get_uiautomator2():
    """获取 uiautomator2 设备实例"""
    global _device
    try:
        import uiautomator2 as u2
        if _device is None:
            _device = u2.connect()
        return _device
    except Exception as e:
        raise ConnectionError(f"连接 Android 设备失败: {e}")


@app.tool()
def connect() -> str:
    """连接 Android 真机 (USB 调试模式)"""
    try:
        device = get_uiautomator2()
        info = device.info
        
        return json.dumps({
            "status": "connected",
            "device": info.get("productName", "Unknown"),
            "androidVersion": info.get("sdkInt", "Unknown"),
            "manufacturer": info.get("product", "Unknown"),
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def disconnect() -> str:
    """断开 Android 真机连接"""
    global _device, _scrcpy_process
    _device = None
    
    if _scrcpy_process:
        try:
            _scrcpy_process.terminate()
        except:
            pass
        _scrcpy_process = None
    
    return json.dumps({
        "status": "disconnected"
    }, ensure_ascii=False)


@app.tool()
def click(x: int, y: int) -> str:
    """点击屏幕坐标"""
    try:
        device = get_uiautomator2()
        device.click(x, y)
        return json.dumps({
            "status": "ok",
            "action": "click",
            "position": {"x": x, "y": y}
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def swipe(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> str:
    """滑动屏幕"""
    try:
        device = get_uiautomator2()
        device.swipe(x1, y1, x2, y2, duration)
        return json.dumps({
            "status": "ok",
            "action": "swipe",
            "from": {"x": x1, "y": y1},
            "to": {"x": x2, "y": y2}
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def input_text(text: str) -> str:
    """输入文本"""
    try:
        device = get_uiautomator2()
        device.clear_text()
        device.send_keys(text)
        return json.dumps({
            "status": "ok",
            "action": "input",
            "text": text
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def press(key: str) -> str:
    """按下物理按键"""
    try:
        device = get_uiautomator2()
        key_map = {
            "home": device.press("home"),
            "back": device.press("back"),
            "menu": device.press("menu"),
            "power": device.press("power"),
            "volume_up": device.press("volumeup"),
            "volume_down": device.press("volumedown"),
        }
        action = key_map.get(key.lower())
        if action is None:
            return json.dumps({
                "status": "error",
                "message": f"未知按键: {key}"
            }, ensure_ascii=False)
        
        return json.dumps({
            "status": "ok",
            "action": "press",
            "key": key
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def screenshot(path: str = "/tmp/android_phone_screen.png") -> str:
    """截图"""
    try:
        device = get_uiautomator2()
        device.screenshot(path)
        
        # 检查文件是否存在
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            return json.dumps({
                "status": "ok",
                "path": path,
                "size": file_size
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "status": "error",
                "message": "截图文件未生成"
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def get_info() -> str:
    """获取设备信息"""
    try:
        device = get_uiautomator2()
        info = device.info
        
        return json.dumps({
            "status": "ok",
            "info": info
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def start_scrcpy() -> str:
    """启动 scrcpy 投屏"""
    global _scrcpy_process
    try:
        # 检查 scrcpy 是否可用
        result = subprocess.run(["which", "scrcpy"], capture_output=True, text=True)
        if result.returncode != 0:
            return json.dumps({
                "status": "error",
                "message": "scrcpy 未安装"
            }, ensure_ascii=False)
        
        # 启动 scrcpy (无头模式用于自动化)
        _scrcpy_process = subprocess.Popen(
            ["scrcpy", "--turn-screen-off"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return json.dumps({
            "status": "ok",
            "message": "scrcpy 已启动"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@app.tool()
def stop_scrcpy() -> str:
    """停止 scrcpy 投屏"""
    global _scrcpy_process
    try:
        if _scrcpy_process:
            _scrcpy_process.terminate()
            _scrcpy_process = None
        
        return json.dumps({
            "status": "ok",
            "message": "scrcpy 已停止"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


if __name__ == "__main__":
    app.run()
