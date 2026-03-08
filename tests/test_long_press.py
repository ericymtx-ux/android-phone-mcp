"""
Android Controller 测试 - long_press 功能
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from android_phone.core.controller import AndroidController


class TestLongPress:
    """测试 long_press 功能"""

    def test_long_press_with_long_click_method(self):
        """测试当 device 有 long_click 方法时使用它"""
        controller = AndroidController()
        mock_device = Mock()
        mock_device.long_click = Mock(return_value=None)
        controller._device = mock_device
        
        result = controller.long_press(500, 700)
        
        assert result is True
        mock_device.long_click.assert_called_once_with(500, 700, duration=0.8)

    def test_long_press_fallback_to_swipe(self):
        """测试当 device 没有 long_click 时使用 swipe 模拟"""
        controller = AndroidController()
        mock_device = Mock()
        # 没有 long_click 属性
        del mock_device.long_click
        mock_device.swipe = Mock(return_value=None)
        controller._device = mock_device
        
        result = controller.long_press(300, 400, duration=1.0)
        
        assert result is True
        mock_device.swipe.assert_called_once_with(300, 400, 300, 400, 1.0)

    def test_long_press_failure_handling(self):
        """测试 long_press 失败时返回 False"""
        controller = AndroidController()
        mock_device = Mock()
        mock_device.long_click = Mock(side_effect=Exception("Device error"))
        controller._device = mock_device
        
        result = controller.long_press(100, 200)
        
        assert result is False

    def test_long_press_default_duration(self):
        """测试默认 duration 为 0.8 秒"""
        controller = AndroidController()
        mock_device = Mock()
        mock_device.long_click = Mock(return_value=None)
        controller._device = mock_device
        
        controller.long_press(500, 500)
        
        # 验证使用了默认 duration
        call_kwargs = mock_device.long_click.call_args
        assert call_kwargs.kwargs['duration'] == 0.8

    def test_long_press_custom_duration(self):
        """测试自定义 duration"""
        controller = AndroidController()
        mock_device = Mock()
        mock_device.long_click = Mock(return_value=None)
        controller._device = mock_device
        
        controller.long_press(500, 500, duration=1.5)
        
        call_kwargs = mock_device.long_click.call_args
        assert call_kwargs.kwargs['duration'] == 1.5


class TestAgentLongPress:
    """测试 Agent 中的 long_press 处理"""

    def test_handle_long_press(self):
        """测试 _handle_long_press 方法"""
        from android_phone.core.agent import AutonomousAgent
        
        mock_controller = Mock()
        mock_controller.long_press = Mock(return_value=True)
        mock_controller.denormalize_coordinates = Mock(return_value=(500, 700))
        
        agent = AutonomousAgent(mock_controller, Mock())
        
        action = {"x": 500, "y": 700}
        result = agent._handle_long_press(action)
        
        assert result is True
        mock_controller.long_press.assert_called_once_with(500, 700)

    def test_handle_long_press_missing_coords(self):
        """测试缺少坐标时返回 False"""
        from android_phone.core.agent import AutonomousAgent
        
        mock_controller = Mock()
        agent = AutonomousAgent(mock_controller, Mock())
        
        # 缺少 x
        action = {"y": 700}
        result = agent._handle_long_press(action)
        assert result is False
        
        # 缺少 y
        action = {"x": 500}
        result = agent._handle_long_press(action)
        assert result is False

    def test_handle_long_press_denormalize(self):
        """测试坐标反归一化"""
        from android_phone.core.agent import AutonomousAgent
        
        mock_controller = Mock()
        # 模拟从归一化坐标 (500/1000, 700/1000) 转换为像素坐标
        mock_controller.denormalize_coordinates = Mock(return_value=(540, 960))
        mock_controller.long_press = Mock(return_value=True)
        
        agent = AutonomousAgent(mock_controller, Mock())
        
        action = {"x": 500, "y": 700}
        result = agent._handle_long_press(action)
        
        assert result is True
        mock_controller.denormalize_coordinates.assert_called_once_with(500, 700, scale=1000)
        mock_controller.long_press.assert_called_once_with(540, 960)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
