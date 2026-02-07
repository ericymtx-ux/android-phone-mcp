import time
import random
import logging
import os
from typing import Dict, Any, Optional

from android_phone.core.controller import AndroidController
from android_phone.integrations.volcengine import VolcengineGUIClient
from android_phone.integrations.parser import parse_action_from_text

logger = logging.getLogger(__name__)

class AutonomousAgent:
    def __init__(self, controller: AndroidController, client: VolcengineGUIClient):
        self.controller = controller
        self.client = client
        self.screenshot_dir = os.path.join(os.getcwd(), ".active_screenshots")
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir, exist_ok=True)

    def run(self, goal: str, max_steps: int = 50) -> str:
        """
        Run the autonomous task loop.
        """
        logger.info(f"Starting autonomous task: {goal}")
        
        # 1. Reset Session
        self.client.reset_session()
        
        # Initial instruction
        instruction = goal
        
        for step in range(max_steps):
            logger.info(f"Step {step + 1}/{max_steps}")
            
            # 2. Capture Screenshot
            # Use lower quality/scale for API efficiency if needed, but 720p is good
            try:
                # scale=0.5 for speed and token saving (usually sufficient for UI)
                image_b64 = self.controller.get_screenshot(scale=0.5, quality=60)
            except Exception as e:
                logger.error(f"Failed to capture screenshot: {e}")
                return f"Error: Failed to capture screenshot - {e}"

            # 3. Call Volcengine
            try:
                # parsed_result contains 'thought' and 'action_parsed'
                response = self.client.ask(instruction, image_b64)
            except Exception as e:
                logger.error(f"Volcengine API failed: {e}")
                return f"Error: Volcengine API failed - {e}"

            # 4. Parse and Execute
            action_data = response.get("action_parsed")
            thought = response.get("thought")
            raw_content = response.get("raw_content", "")
            
            logger.info(f"Thought: {thought}")
            if not action_data:
                logger.warning(f"No structured action found. Raw content: {raw_content}")
                instruction = (
                    "Error: I could not parse your previous output. "
                    "Please provide the next step strictly in the format:\n"
                    "Thought: ...\n"
                    "Action: function(...)\n"
                    "Example: Action: click(point='<point>500 500</point>')"
                )
                continue

            action_type = action_data.get("type")
            logger.info(f"Executing Action: {action_type} - {action_data}")

            result_msg = ""
            
            if action_type == "finished":
                content = action_data.get("content", "")
                logger.info(f"Task Finished: {content}")
                return f"Task Completed: {content}"
            
            elif action_type == "click":
                success = self._handle_click(action_data)
                result_msg = "Click successful" if success else "Click failed"
                
            elif action_type == "left_double":
                # Double click
                success = self._handle_click(action_data, double=True)
                result_msg = "Double click successful" if success else "Double click failed"

            elif action_type == "right_single":
                # Right click (usually long press or context menu on Android, but u2 has no right click)
                # Map to normal click or long click? Prompt says "right_single".
                # Let's map to normal click for now or ignore.
                success = self._handle_click(action_data)
                result_msg = "Right click (mapped to tap) successful" if success else "Right click failed"

            elif action_type == "type":
                content = action_data.get("content", "")
                success = self.controller.input_text(content)
                result_msg = f"Typed '{content}' successful" if success else "Type failed"
                
            elif action_type == "scroll":
                success = self._handle_scroll(action_data)
                result_msg = "Scroll successful" if success else "Scroll failed"
                
            elif action_type == "drag":
                success = self._handle_drag(action_data)
                result_msg = "Drag successful" if success else "Drag failed"
                
            elif action_type == "hotkey":
                key = action_data.get("key", "")
                success = self.controller.press_key(key)
                result_msg = f"Pressed key '{key}' successful" if success else "Key press failed"
                
            elif action_type == "wait":
                time.sleep(5)
                result_msg = "Waited 5 seconds"
                
            elif action_type == "screenshot":
                filename = action_data.get("filename")
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                
                if not filename:
                    filename = f"screenshot_{timestamp}.png"
                else:
                    # Strip extension
                    base_name = os.path.splitext(filename)[0]
                    filename = f"{base_name}_{timestamp}.png"
                
                # Force save to screenshot_dir
                save_path = os.path.join(self.screenshot_dir, os.path.basename(filename))
                
                try:
                    self.controller.get_screenshot(save_path=save_path)
                    result_msg = f"Screenshot saved to {save_path}"
                    logger.info(result_msg)
                except Exception as e:
                    logger.error(f"Failed to save screenshot: {e}")
                    result_msg = f"Failed to save screenshot: {e}"

            else:
                result_msg = f"Unknown action type: {action_type}"
                logger.warning(result_msg)

            # Update instruction for next turn
            instruction = f"Action '{action_type}' executed. Result: {result_msg}. Continue to {goal}."
            
            # Short wait for UI to settle (random 0.5-3.5s)
            sleep_time = random.uniform(0.5, 3.5)
            logger.info(f"Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

        return "Max steps reached without completion."

    def _denormalize(self, x: int, y: int) -> tuple[int, int]:
        return self.controller.denormalize_coordinates(x, y, scale=1000)

    def _handle_click(self, action: Dict[str, Any], double: bool = False) -> bool:
        x = action.get("x")
        y = action.get("y")
        if x is None or y is None:
            return False
        
        px, py = self._denormalize(x, y)
        if double:
            # u2 doesn't have explicit double click on coords in basic wrapper, 
            # but we can do click twice.
            # self.controller.device.double_click(x, y) if exposed.
            # AndroidController wraps device.
            try:
                self.controller.device.double_click(px, py)
                return True
            except:
                self.controller.click(px, py)
                time.sleep(0.1)
                return self.controller.click(px, py)
        else:
            return self.controller.click(px, py)

    def _handle_scroll(self, action: Dict[str, Any]) -> bool:
        # scroll(point='<point>x1 y1</point>', direction='down')
        # prompt: "Show more information on the `direction` side."
        direction = action.get("direction", "down").lower()
        
        # Default center if point not provided
        w, h = self.controller.device.window_size()
        start_x = w // 2
        start_y = h // 2
        
        if "x" in action and "y" in action:
            start_x, start_y = self._denormalize(action["x"], action["y"])

        # Calculate swipe
        # Scroll Down -> Swipe Up (show content below)
        # Scroll Up -> Swipe Down (show content above)
        
        delta_y = h // 3
        delta_x = w // 3
        
        end_x, end_y = start_x, start_y
        
        if direction == "down":
            end_y = start_y - delta_y
        elif direction == "up":
            end_y = start_y + delta_y
        elif direction == "right":
            # Scroll Right -> Swipe Left (show content on right)
            end_x = start_x - delta_x
        elif direction == "left":
            # Scroll Left -> Swipe Right (show content on left)
            end_x = start_x + delta_x
            
        return self.controller.swipe(start_x, start_y, end_x, end_y)

    def _handle_drag(self, action: Dict[str, Any]) -> bool:
        start_x = action.get("start_x")
        start_y = action.get("start_y")
        end_x = action.get("end_x")
        end_y = action.get("end_y")
        
        if any(v is None for v in [start_x, start_y, end_x, end_y]):
            return False
            
        sx, sy = self._denormalize(start_x, start_y)
        ex, ey = self._denormalize(end_x, end_y)
        
        return self.controller.swipe(sx, sy, ex, ey)
