#!/usr/bin/env python3
"""
Android Phone MCP - Device Verification Script
用于验证设备连接、截图、XML获取等核心功能是否正常。
"""

import sys
import os
import base64
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from android_phone.core.controller import AndroidController

def main():
    print("📱 Android Device Verification Tool")
    print("===================================")
    
    try:
        controller = AndroidController()
        
        # 1. Connect
        print("\n[1/5] Connecting to device...")
        if not controller.connect():
            print("❌ Connection failed! Please check USB connection and ADB.")
            return
        
        info = controller.get_info()
        print(f"✅ Connected: {info.get('productName')} ({info.get('product')})")
        print(f"   SDK: {info.get('sdkInt')}")
        print(f"   Screen: {info.get('displayWidth')}x{info.get('displayHeight')}")

        # 2. Screenshot
        print("\n[2/5] Testing Screenshot...")
        try:
            # Test scale 0.5
            b64_img = controller.get_screenshot(scale=0.5, quality=60)
            img_data = base64.b64decode(b64_img)
            output_path = "verify_screenshot.jpg"
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"✅ Screenshot saved to: {output_path} ({len(img_data)/1024:.1f} KB)")
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")

        # 3. XML Hierarchy
        print("\n[3/5] Testing UI Hierarchy...")
        try:
            # Full XML
            # xml = controller.get_ui_hierarchy()
            # print(f"   Full XML length: {len(xml)} chars")
            
            # Compact XML
            compact_xml = controller.get_compact_ui_hierarchy()
            print(f"✅ Compact XML fetched ({len(compact_xml)} chars)")
            print(f"   Preview: {compact_xml[:200]}...")
        except Exception as e:
            print(f"❌ XML fetch failed: {e}")

        # 4. App List
        print("\n[4/5] Listing Apps...")
        try:
            apps = controller.list_apps()
            print(f"✅ Found {len(apps)} third-party apps")
            if apps:
                print(f"   Examples: {', '.join(apps[:3])}")
        except Exception as e:
            print(f"❌ List apps failed: {e}")

        # 5. Coordinate Test (Dry Run)
        print("\n[5/5] Testing Coordinate Conversion...")
        try:
            w, h = info.get('displayWidth'), info.get('displayHeight')
            cx, cy = w // 2, h // 2
            nx, ny = controller.normalize_coordinates(cx, cy)
            print(f"✅ Center ({cx}, {cy}) -> Normalized ({nx}, {ny})")
            
            # Verify inverse
            rx, ry = controller.denormalize_coordinates(nx, ny)
            print(f"   Inverse ({nx}, {ny}) -> Pixel ({rx}, {ry})")
            
            if abs(rx - cx) < 2 and abs(ry - cy) < 2:
                print("   Precision OK")
            else:
                print("⚠️ Precision Warning")
        except Exception as e:
            print(f"❌ Coordinate test failed: {e}")

        print("\n🎉 Verification Complete!")

    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")

if __name__ == "__main__":
    main()
