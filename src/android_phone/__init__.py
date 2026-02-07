"""Android Phone MCP Server"""

try:
    from .server import app
    __all__ = ["app"]
except ImportError:
    pass
