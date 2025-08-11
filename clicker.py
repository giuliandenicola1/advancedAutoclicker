"""
Mouse click simulation for autoclicker - handles precise clicking at detected positions.
"""

import pyautogui
import time
from typing import Tuple
from config import Rule, Condition
from logger import get_logger


class MouseClicker:
    """Handles mouse click simulation at specific screen positions"""
    
    def __init__(self):
        """Initialize the mouse clicker"""
        # Configure pyautogui settings
        pyautogui.FAILSAFE = True  # Enable failsafe (move mouse to corner to abort)
        pyautogui.PAUSE = 0.1  # Small pause between actions for reliability
        
        # Click settings
        self.click_duration = 0.1  # Duration to hold mouse button down
        self.double_click_interval = 0.25  # Interval between double clicks
        
        # Initialize logger
        self.logger = get_logger()
        
    def click_at_position(self, position: Tuple[int, int], 
                         click_type: str = 'single', 
                         button: str = 'left') -> bool:
        """
        Perform a mouse click at the specified position.
        
        Args:
            position: (x, y) coordinates to click
            click_type: Type of click ('single', 'double', 'right')
            button: Mouse button to use ('left', 'right', 'middle')
            
        Returns:
            True if click was successful, False otherwise
        """
        try:
            x, y = position
            
            # Validate coordinates are within screen bounds
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x < screen_width and 0 <= y < screen_height):
                print(f"Error: Position {position} is outside screen bounds ({screen_width}x{screen_height})")
                return False
            
            print(f"Performing {click_type} {button} click at position ({x}, {y})")
            
            # Move mouse to position first
            pyautogui.moveTo(x, y, duration=0.2)
            
            # Perform the click based on type
            if click_type == 'single':
                pyautogui.click(x, y, button=button, duration=self.click_duration)
            elif click_type == 'double':
                pyautogui.doubleClick(x, y, interval=self.double_click_interval)
            elif click_type == 'right':
                pyautogui.rightClick(x, y)
            else:
                print(f"Warning: Unknown click type '{click_type}', using single click")
                pyautogui.click(x, y, button=button, duration=self.click_duration)
            
            print(f"✅ Successfully clicked at ({x}, {y})")
            self.logger.log_click(position, click_type, success=True)
            return True
            
        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI FailSafe triggered - mouse moved to corner"
            print(f"❌ {error_msg}")
            self.logger.log_error(error_msg, "clicker")
            self.logger.log_click(position, click_type, success=False)
            return False
        except Exception as e:
            error_msg = f"Error performing click: {e}"
            print(f"❌ {error_msg}")
            self.logger.log_error(error_msg, "clicker", e)
            self.logger.log_click(position, click_type, success=False)
            return False
    
    def click_for_rule(self, rule: Rule, click_type: str = 'single') -> bool:
        """
        Perform a click based on a matched rule's click position.
        
        Args:
            rule: The matched rule containing click position
            click_type: Type of click to perform
            
        Returns:
            True if any click was successful, False otherwise
        """
        # Use dedicated click_position if available
        if hasattr(rule, 'click_position') and rule.click_position:
            click_position = rule.click_position
            print(f"Using dedicated click position: {click_position}")
        # Legacy fallback to first condition position
        elif hasattr(rule, 'conditions') and rule.conditions:
            click_position = rule.conditions[0].position
            print(f"Using first condition position for click: {click_position}")
            # For area positions, use center of area
            if len(click_position) == 4:
                x1, y1, x2, y2 = click_position
                click_position = ((x1 + x2) // 2, (y1 + y2) // 2)
                print(f"Using center of area for click: {click_position}")
        else:
            print("Error: No position available in rule for clicking")
            return False
            
        # Perform the click at the determined position
        return self.click_at_position(click_position, click_type)
    
    def click_for_conditions(self, conditions: list[Condition], 
                           strategy: str = 'first') -> bool:
        """
        Perform clicks based on multiple conditions.
        
        Args:
            conditions: List of conditions with positions
            strategy: Strategy for choosing click position
                     'first' - use first condition's position
                     'center' - use center of all positions
                     'all' - click at all positions
                     
        Returns:
            True if successful, False otherwise
        """
        if not conditions:
            print("Error: No conditions provided")
            return False
        
        if strategy == 'first':
            return self.click_at_position(conditions[0].position)
        
        elif strategy == 'center':
            # Calculate center position of all conditions
            positions = [cond.position for cond in conditions]
            center_x = sum(pos[0] for pos in positions) // len(positions)
            center_y = sum(pos[1] for pos in positions) // len(positions)
            return self.click_at_position((center_x, center_y))
        
        elif strategy == 'all':
            # Click at all condition positions
            success_count = 0
            for condition in conditions:
                if self.click_at_position(condition.position):
                    success_count += 1
                time.sleep(0.2)  # Small delay between clicks
            
            return success_count > 0
        
        else:
            print(f"Unknown strategy '{strategy}', using 'first'")
            return self.click_at_position(conditions[0].position)
    
    def simulate_button_click(self, position: Tuple[int, int]) -> bool:
        """
        Simulate a button click with hover effect for better reliability.
        
        Args:
            position: (x, y) coordinates of the button
            
        Returns:
            True if successful, False otherwise
        """
        try:
            x, y = position
            
            # Move to position and hover briefly
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.1)  # Brief hover
            
            # Perform click with slight press and release
            pyautogui.mouseDown(x, y, button='left')
            time.sleep(self.click_duration)
            pyautogui.mouseUp(x, y, button='left')
            
            print(f"✅ Button click simulated at ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ Error simulating button click: {e}")
            return False
    
    def get_current_mouse_position(self) -> Tuple[int, int]:
        """
        Get the current mouse cursor position.
        
        Returns:
            Current (x, y) position of mouse cursor
        """
        return pyautogui.position()
    
    def is_position_clickable(self, position: Tuple[int, int]) -> bool:
        """
        Check if a position is within clickable screen bounds.
        
        Args:
            position: (x, y) coordinates to check
            
        Returns:
            True if position is clickable, False otherwise
        """
        try:
            x, y = position
            screen_width, screen_height = pyautogui.size()
            return 0 <= x < screen_width and 0 <= y < screen_height
        except Exception:
            return False
    
    def configure_click_settings(self, duration: float = 0.1, 
                                pause: float = 0.1, 
                                failsafe: bool = True) -> None:
        """
        Configure click behavior settings.
        
        Args:
            duration: Duration to hold mouse button down
            pause: Pause between pyautogui actions
            failsafe: Enable/disable failsafe feature
        """
        self.click_duration = duration
        pyautogui.PAUSE = pause
        pyautogui.FAILSAFE = failsafe
        
        print(f"Click settings updated: duration={duration}s, pause={pause}s, failsafe={failsafe}")
    
    def test_click_area(self, center: Tuple[int, int], radius: int = 5) -> bool:
        """
        Test clicking in a small area around a center point.
        Useful for testing if a button/element is clickable.
        
        Args:
            center: Center position to test around
            radius: Radius of area to test (pixels)
            
        Returns:
            True if any position in area is clickable
        """
        center_x, center_y = center
        
        # Test center position first
        if self.is_position_clickable(center):
            return True
        
        # Test positions in a small radius around center
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                test_pos = (center_x + dx, center_y + dy)
                if self.is_position_clickable(test_pos):
                    return True
        
        return False
