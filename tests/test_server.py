"""Android Phone MCP Server 测试"""

import pytest
import sys
from pathlib import Path


def test_import():
    """测试服务器导入"""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from android_phone.server import app
    assert app is not None
    print("✓ MCP server 导入成功")


def test_server_name():
    """测试服务器名称"""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from android_phone.server import app
    assert app.name == "android-phone-mcp"
    print("✓ 服务器名称正确: android-phone-mcp")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
