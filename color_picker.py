#!/usr/bin/env python3
"""
Real-time Color Picker - Get RGB values at current mouse position
Press 'q' to quit, 'c' to copy current color to clipboard
"""

import pyautogui
import time
import sys


def get_mouse_color():
    """Get RGB color at current mouse position"""
    try:
        # Get current mouse position
        x, y = pyautogui.position()
        
        # Take screenshot of 1x1 pixel at mouse position
        screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
        
        # Get RGB values
        rgb = screenshot.getpixel((0, 0))
        
        return x, y, rgb
    except Exception as e:
        print(f"Error getting color: {e}")
        return None, None, None


def main():
    """Main function for real-time color picking"""
    print("🎨 Real-time Color Picker")
    print("=" * 40)
    print("Move your mouse to see RGB values")
    print("Press Ctrl+C to quit")
    print("-" * 40)
    
    last_position = None
    last_color = None
    
    try:
        while True:
            x, y, rgb = get_mouse_color()
            
            if x is not None and (x, y) != last_position:
                last_position = (x, y)
                last_color = rgb
                
                # Clear line and print new info
                print(f"\r📍 Position: ({x:4d}, {y:4d}) | 🎨 RGB: {rgb}     ", end="", flush=True)
            
            time.sleep(0.1)  # Update 10 times per second
            
    except KeyboardInterrupt:
        print(f"\n\n🏁 Final position: ({last_position[0]}, {last_position[1]})")
        print(f"🎨 Final color: RGB{last_color}")
        print(f"📋 For autoclicker: Position=({last_position[0]}, {last_position[1]}), Color={last_color}")
        print("\nGoodbye! 👋")


if __name__ == "__main__":
    main()
