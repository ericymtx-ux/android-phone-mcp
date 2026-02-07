import base64
import io
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, Dict, Any, List
import uiautomator2 as u2
from PIL import Image

logger = logging.getLogger(__name__)

class AndroidController:
    """
    Android Device Controller wrapping uiautomator2.
    Handles connection, action execution, and state observation.
    """
    
    def __init__(self, serial: Optional[str] = None):
        self.serial = serial
        self._device = None
        
    @property
    def device(self):
        """Lazy connection to the device."""
        if self._device is None:
            self.connect()
        return self._device

    def connect(self) -> bool:
        """Connect to the Android device."""
        try:
            logger.info(f"Connecting to device {self.serial if self.serial else '(default)'}...")
            self._device = u2.connect(self.serial)
            logger.info(f"Connected: {self._device.info.get('productName')}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Android device: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self.device.info

    def normalize_coordinates(self, x: int, y: int, scale: int = 1000) -> Tuple[int, int]:
        """
        Convert pixel coordinates to normalized coordinates (0-scale).
        """
        w, h = self.device.window_size()
        norm_x = int((x / w) * scale)
        norm_y = int((y / h) * scale)
        return (norm_x, norm_y)

    def denormalize_coordinates(self, norm_x: int, norm_y: int, scale: int = 1000) -> Tuple[int, int]:
        """
        Convert normalized coordinates (0-scale) to pixel coordinates.
        """
        w, h = self.device.window_size()
        x = int((norm_x / scale) * w)
        y = int((norm_y / scale) * h)
        return (x, y)

    def get_screenshot(self, quality: int = 70, max_size: Tuple[int, int] = (1080, 1920), scale: float = 1.0, save_path: str = None) -> str:
        """
        Capture screenshot and return as base64 string.
        
        Args:
            quality: JPEG quality (1-100).
            max_size: Max (width, height) to resize to. Preserves aspect ratio.
            scale: Scaling factor (0.1 to 1.0). Applied BEFORE max_size constraint.
            save_path: If provided, save the screenshot to this path (PNG or JPEG).
        """
        try:
            # uiautomator2 returns PIL Image by default with format='pillow'
            # But the default screenshot() method saves to file. 
            # We use screenshot(format='pillow') or underlying method if available.
            # Actually u2.screenshot() returns a PIL Image object if filename is not provided (in newer versions)
            # or we can use d.screenshot(format='opencv') and convert.
            # Let's try standard way.
            
            # Temporary file approach is safest across versions, but slow.
            # Let's try in-memory.
            image = self.device.screenshot(format='pillow')
            
            # Save original if requested
            if save_path:
                image.save(save_path)
                logger.info(f"Screenshot saved to {save_path}")
            
            # Apply scale first if needed
            if scale < 1.0 and scale > 0:
                new_w = int(image.size[0] * scale)
                new_h = int(image.size[1] * scale)
                image.thumbnail((new_w, new_h), Image.Resampling.LANCZOS)

            # Resize if needed
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
            # Convert to JPEG bytes
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            image_bytes = buffer.getvalue()
            
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise RuntimeError(f"Failed to capture screenshot: {e}")

    def get_ui_hierarchy(self, compressed: bool = True) -> str:
        """
        Get UI hierarchy as XML string.
        
        Args:
            compressed: If True, performs basic compression (not yet implemented fully, returns raw).
        """
        try:
            xml_content = self.device.dump_hierarchy(compressed=compressed)
            return xml_content
        except Exception as e:
            logger.error(f"Dump hierarchy failed: {e}")
            raise RuntimeError(f"Failed to get UI hierarchy: {e}")

    def get_compact_ui_hierarchy(self) -> str:
        """
        Get a simplified UI hierarchy XML to reduce context size.
        Only keeps visible, useful nodes.
        """
        try:
            raw_xml = self.device.dump_hierarchy(compressed=True)
            root = ET.fromstring(raw_xml)
            
            def filter_node(node):
                # Keep list for children to remove
                to_remove = []
                
                # Check attributes
                # U2 XML attributes often use lowercase keys directly like 'text', 'resource-id' or 'resource-id'
                # Note: The actual dump might have keys like 'resource-id', 'text', 'class', 'package', 'content-desc', 'checkable', 'checked', 'clickable', 'enabled', 'focusable', 'focused', 'scrollable', 'long-clickable', 'password', 'selected', 'bounds'
                
                # Filter logic:
                # 1. Remove invisible nodes (Wait, u2 dump usually only contains visible hierarchy? Not always)
                # Let's assume we keep structure but remove redundant attributes first.
                
                # Attributes to keep
                keep_attrs = ['text', 'resource-id', 'content-desc', 'bounds', 'checked', 'class']
                # If clickable/scrollable/editable is true, keep them too as hints
                hint_attrs = ['clickable', 'scrollable', 'editable', 'long-clickable']
                
                new_attrib = {}
                for k, v in node.attrib.items():
                    if k in keep_attrs:
                        # Only keep non-empty text/resource-id
                        if k in ['text', 'resource-id', 'content-desc'] and not v:
                            continue
                        new_attrib[k] = v
                    elif k in hint_attrs and v == 'true':
                         new_attrib[k] = v
                
                node.attrib = new_attrib
                
                # Recursive filter
                for child in node:
                    filter_node(child)
                    
                # Simplification: 
                # If a node has no text, no id, no desc, and is not clickable/scrollable, 
                # AND has no children (or children were removed), we might want to prune it?
                # But layout structure is important for VLM to understand "where" things are.
                # So maybe we just keep the filtered attributes.
                
            filter_node(root)
            
            # Convert back to string
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            logger.error(f"Compact hierarchy failed: {e}")
            # Fallback to raw
            return self.get_ui_hierarchy()

    def click_element(self, text: str = None, resource_id: str = None, timeout: float = 10.0) -> bool:
        """
        Click an element by text or resource_id.
        
        Args:
            text: Text content of the element.
            resource_id: Resource ID of the element.
            timeout: Max wait time in seconds.
        """
        try:
            if not text and not resource_id:
                logger.error("click_element requires either text or resource_id")
                return False

            # Selector
            if text:
                d = self.device(text=text)
            else:
                d = self.device(resourceId=resource_id)
            
            # Wait and click
            if d.exists(timeout=timeout):
                d.click()
                logger.info(f"Clicked element: text={text}, id={resource_id}")
                return True
            else:
                logger.warning(f"Element not found: text={text}, id={resource_id}")
                return False
        except Exception as e:
            logger.error(f"Click element failed: {e}")
            return False

    def click(self, x: int, y: int) -> bool:
        """Click at coordinates."""
        try:
            self.device.click(x, y)
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> bool:
        """Swipe from (x1, y1) to (x2, y2)."""
        try:
            self.device.swipe(x1, y1, x2, y2, duration)
            return True
        except Exception as e:
            logger.error(f"Swipe failed: {e}")
            return False

    def input_text(self, text: str, clear: bool = True) -> bool:
        """Input text."""
        try:
            if clear:
                self.device.clear_text()
            self.device.send_keys(text)
            return True
        except Exception as e:
            logger.error(f"Input text failed: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """Press a physical key."""
        try:
            # Map common names to u2 key names if needed, but u2 handles most
            valid_keys = ['home', 'back', 'left', 'right', 'up', 'down', 'center', 
                          'menu', 'search', 'enter', 'delete', 'recent', 'volume_up', 'volume_down', 'camera', 'power']
            
            # Normalize key name
            key_lower = key.lower().strip()
            
            # Common mappings for Chinese or variations
            mappings = {
                "home键": "home",
                "主页": "home",
                "主页键": "home",
                "返回": "back",
                "返回键": "back",
                "回车": "enter",
                "搜索": "search",
                "菜单": "menu"
            }
            
            if key_lower in mappings:
                key_lower = mappings[key_lower]
            
            if key_lower not in valid_keys:
                 # Try passing it directly, u2 might support key codes
                 # If it's a known mapped key but not in valid_keys list (unlikely if mappings cover it)
                 pass
            else:
                # Use the valid key name
                key = key_lower
            
            self.device.press(key)
            return True
        except Exception as e:
            logger.error(f"Press key failed: {e}")
            return False

    def launch_app(self, package_name: str) -> bool:
        """Launch an app by package name."""
        try:
            self.device.app_start(package_name)
            return True
        except Exception as e:
            logger.error(f"Launch app failed: {e}")
            return False

    def list_apps(self) -> List[str]:
        """List installed third-party apps."""
        try:
            # u2 app_list_running or similar? u2 app_list() returns list of packages
            # We want third party apps usually.
            # u2 wrapper might not expose everything.
            # Let's use shell command via u2
            output = self.device.shell("pm list packages -3")
            # output format: package:com.example
            packages = [line.replace('package:', '').strip() for line in output.output.splitlines() if line.strip()]
            return packages
        except Exception as e:
            logger.error(f"List apps failed: {e}")
            return []

    def unlock_device(self) -> bool:
        """Try to unlock the device."""
        try:
            self.device.screen_on()
            self.device.unlock() # u2 built-in unlock
            return True
        except Exception as e:
            logger.error(f"Unlock failed: {e}")
            return False

    def stop_app(self, package_name: str) -> bool:
        """Stop an app."""
        try:
            self.device.app_stop(package_name)
            return True
        except Exception as e:
            logger.error(f"Stop app failed: {e}")
            return False
