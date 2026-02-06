import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from android_phone.core.controller import AndroidController

class TestAndroidController(unittest.TestCase):
    
    def setUp(self):
        self.controller = AndroidController()
        # Mock the u2 device
        self.controller._device = MagicMock()
        
    def test_compact_xml_filtering(self):
        """Test if the XML simplification logic works correctly."""
        
        # A mock XML with various attributes and nodes
        # 1. Visible, useful node (Text) -> Keep
        # 2. Visible, useful node (Resource ID) -> Keep
        # 3. Visible container (Scrollable) -> Keep structure, keep scrollable=true
        # 4. Useless container (just bounds) -> Attributes should be stripped? Or node removed?
        #    Currently our logic keeps the node but strips useless attributes.
        
        raw_xml = """
        <hierarchy rotation="0">
            <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.launcher3" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,0][1080,1920]">
                <node index="0" text="Google" resource-id="com.google.android.googlequicksearchbox:id/text_content" class="android.widget.TextView" package="com.google.android.googlequicksearchbox" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[66,135][918,297]" />
                <node index="1" text="" resource-id="" class="android.view.View" package="com.android.launcher3" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="true" long-clickable="false" password="false" selected="false" bounds="[0,0][1080,1920]" />
            </node>
        </hierarchy>
        """
        
        # Mock the dump_hierarchy return value
        self.controller._device.dump_hierarchy.return_value = raw_xml
        
        compact_xml = self.controller.get_compact_ui_hierarchy()
        
        print(f"Original XML len: {len(raw_xml)}")
        print(f"Compact XML len: {len(compact_xml)}")
        print("Compact XML Content:")
        print(compact_xml)
        
        root = ET.fromstring(compact_xml)
        
        # Verify Node 0 (Root) - should have minimal attributes
        # bounds is in keep list. text/resource-id empty so should be gone.
        # clickable is false so gone.
        self.assertIn('bounds', root[0].attrib)
        self.assertNotIn('text', root[0].attrib)
        self.assertNotIn('clickable', root[0].attrib)
        
        # Verify Child 0 (Google Text)
        # text="Google" -> Keep
        # resource-id -> Keep
        # clickable="true" -> Keep
        child0 = root[0][0]
        self.assertEqual(child0.attrib['text'], "Google")
        self.assertIn('resource-id', child0.attrib)
        self.assertEqual(child0.attrib['clickable'], 'true')
        self.assertNotIn('password', child0.attrib) # Should be removed
        
        # Verify Child 1 (Scrollable View)
        # scrollable="true" -> Keep
        child1 = root[0][1]
        self.assertEqual(child1.attrib['scrollable'], 'true')
        self.assertNotIn('text', child1.attrib) # Empty text removed

    def test_coordinate_conversion(self):
        """Test coordinate normalization."""
        # Mock window size
        self.controller._device.window_size.return_value = (1080, 1920)
        
        # Test Normalize
        # Center: 540, 960 -> 500, 500
        nx, ny = self.controller.normalize_coordinates(540, 960)
        self.assertEqual(nx, 500)
        self.assertEqual(ny, 500)
        
        # Test Denormalize
        # 500, 500 -> 540, 960
        px, py = self.controller.denormalize_coordinates(500, 500)
        self.assertEqual(px, 540)
        self.assertEqual(py, 960)

if __name__ == '__main__':
    unittest.main()
