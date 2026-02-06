"""
Volcengine Action Parser 测试
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from android_phone.integrations.parser import parse_action_from_text


class TestParseActionFromText:
    """测试 parse_action_from_text 函数"""

    def test_parse_click_action(self):
        """测试点击动作解析"""
        text = """Thought: I need to click on the button at position 500, 300
Action: click(point='<point>500 300</point>')"""
        
        result = parse_action_from_text(text)
        
        assert result["thought"] == "I need to click on the button at position 500, 300"
        assert result["action_raw"] == "click(point='<point>500 300</point>')"
        assert result["action_parsed"]["type"] == "click"
        assert result["action_parsed"]["x"] == 500
        assert result["action_parsed"]["y"] == 300

    def test_parse_type_action(self):
        """测试输入动作解析"""
        text = """Thought: I should type the message
Action: type(content='hello world')"""
        
        result = parse_action_from_text(text)
        
        assert "I should type the message" in result["thought"]
        assert result["action_parsed"]["type"] == "type"
        assert result["action_parsed"]["content"] == "hello world"

    def test_parse_swipe_action(self):
        """测试滑动动作解析"""
        text = """Thought: Swipe up to scroll
Action: swipe(direction='up')"""
        
        result = parse_action_from_text(text)
        
        assert result["action_parsed"]["type"] == "swipe"
        assert result["action_parsed"]["direction"] == "up"

    def test_parse_drag_action(self):
        """测试拖拽动作解析"""
        text = """Thought: Drag from one position to another
Action: drag(start_point='<point>100 200</point>', end_point='<point>400 500</point>')"""
        
        result = parse_action_from_text(text)
        
        assert result["action_parsed"]["type"] == "drag"
        assert result["action_parsed"]["start_x"] == 100
        assert result["action_parsed"]["start_y"] == 200
        assert result["action_parsed"]["end_x"] == 400
        assert result["action_parsed"]["end_y"] == 500

    def test_parse_hotkey_action(self):
        """测试快捷键动作解析"""
        text = """Thought: Press enter to confirm
Action: hotkey(key='enter')"""
        
        result = parse_action_from_text(text)
        
        assert result["action_parsed"]["type"] == "hotkey"
        assert result["action_parsed"]["key"] == "enter"

    def test_parse_finished_action(self):
        """测试完成动作解析"""
        text = """Thought: Task completed
Action: finished(content='Successfully opened the app')"""
        
        result = parse_action_from_text(text)
        
        assert result["action_parsed"]["type"] == "finished"
        assert "Successfully opened the app" in result["action_parsed"]["content"]

    def test_parse_no_action(self):
        """测试无动作情况"""
        text = """Thought: Just thinking"""
        
        result = parse_action_from_text(text)
        
        assert result["thought"] == "Just thinking"
        assert result["action_raw"] is None
        assert result["action_parsed"] is None

    def test_parse_no_thought(self):
        """测试无思考情况"""
        text = """Action: click(point='<point>100 200</point>')"""
        
        result = parse_action_from_text(text)
        
        assert result["thought"] is None
        assert result["action_parsed"]["x"] == 100
        assert result["action_parsed"]["y"] == 200

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        text = """THOUGHT: Test
ACTION: click(point='<point>100 100</point>')"""
        
        result = parse_action_from_text(text)
        
        assert result["thought"] == "Test"
        assert result["action_parsed"]["type"] == "click"

    def test_whitespace_handling(self):
        """测试空白字符处理"""
        text = """Thought:   Extra spaces   
Action:   click(point='<point>50 50</point>')   """
        
        result = parse_action_from_text(text)
        
        assert result["thought"] == "Extra spaces"
        assert result["action_parsed"]["y"] == 50

    def test_complex_mixed_content(self):
        """测试复杂混合内容"""
        text = """Thought: I need to click the submit button and type the verification code
Action: type(content='123456')"""
        
        result = parse_action_from_text(text)
        
        assert "verification code" in result["thought"]
        assert result["action_parsed"]["type"] == "type"
        assert result["action_parsed"]["content"] == "123456"

    def test_multiline_action(self):
        """测试多行动作 (仅测试第一行)"""
        text = """Thought: Complete the form
Action: type(content='John Doe')"""
        
        result = parse_action_from_text(text)
        
        assert "Complete the form" in result["thought"]
        assert result["action_parsed"]["type"] == "type"
        assert result["action_parsed"]["content"] == "John Doe"


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_string(self):
        """测试空字符串"""
        result = parse_action_from_text("")
        
        assert result["thought"] is None
        assert result["action_raw"] is None

    def test_malformed_point(self):
        """测试格式错误的坐标"""
        text = """Action: click(point='<point>abc def</point>')"""
        
        result = parse_action_from_text(text)
        
        # Should not crash, but x/y should not be parsed
        assert result["action_parsed"]["type"] == "click"
        assert "x" not in result["action_parsed"]

    def test_special_characters_in_content(self):
        """测试内容中的特殊字符"""
        text = """Action: type(content='Hello, "World"!')"""
        
        result = parse_action_from_text(text)
        
        # Content parsing stops at first unescaped quote
        assert result["action_parsed"]["type"] == "type"

    def test_unicode_content(self):
        """测试Unicode内容"""
        text = """Action: type(content='你好世界')"""
        
        result = parse_action_from_text(text)
        
        assert result["action_parsed"]["content"] == "你好世界"

    def test_long_content(self):
        """测试长内容"""
        text = """Action: type(content='This is a very long message that might contain special characters like quotes "and" apostrophes')"""
        
        result = parse_action_from_text(text)
        
        # Content parsing is simple and stops at first quote
        assert result["action_parsed"]["type"] == "type"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
