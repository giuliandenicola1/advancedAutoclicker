"""
Detection engine for autoclicker - handles color and text detection at screen positions.
"""

import cv2
import numpy as np
import pytesseract
import pyautogui
import math
from typing import Tuple, Union
from config import Condition


class DetectionEngine:
    """Handles detection of colors and text at specific screen positions"""
    
    def __init__(self):
        # Disable pyautogui failsafe for smoother operation
        pyautogui.FAILSAFE = False
        
        # Verify Tesseract OCR is available
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract OCR detected")
        except Exception as e:
            print(f"⚠️ Warning: Tesseract OCR may not be properly installed: {e}")
            print("Text detection features may not work correctly.")
        
    def capture_screen_region(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], region_size: int = 20) -> np.ndarray:
        """
        Capture a region from the screen.
        
        Args:
            position: Either (x, y) for point selection or (x1, y1, x2, y2) for area selection
            region_size: Size of the region to capture around point (ignored for area selection)
            
        Returns:
            numpy array representing the captured image region
        """
        if len(position) == 4:
            # Area selection: (x1, y1, x2, y2)
            x1, y1, x2, y2 = position
            left, top = x1, y1
            width = x2 - x1
            height = y2 - y1
        else:
            # Point selection: (x, y)
            x, y = position
            # Calculate region bounds around the point
            left = max(0, x - region_size // 2)
            top = max(0, y - region_size // 2)
            width = region_size
            height = region_size
        
        # Capture screenshot of the region
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        
        # Convert PIL image to numpy array for OpenCV
        img_array = np.array(screenshot)
        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_bgr
    
    def detect_color(self, condition: Condition) -> bool:
        """
        Detect if a specific color is present at the given position.
        
        Args:
            condition: Condition object containing color detection parameters
            
        Returns:
            True if color matches within tolerance, False otherwise
        """
        if condition.type != 'color':
            raise ValueError("Condition type must be 'color' for color detection")
        
        if not isinstance(condition.value, tuple) or len(condition.value) != 3:
            raise ValueError("Color value must be RGB tuple (r, g, b)")
        
        target_color = condition.value  # Define target_color here
        
        # Capture region (either around point or exact area)
        img_region = self.capture_screen_region(condition.position)
        
        # For point selection, get center pixel; for area selection, check if color exists anywhere
        if len(condition.position) == 4:
            # Area selection: check if target color exists anywhere in the area
            print(f"  🔍 Scanning area {condition.position} for color RGB{target_color}")
            return self._color_exists_in_region(img_region, target_color, condition.tolerance, condition.comparator)
        else:
            # Point selection: check center pixel
            center_y, center_x = img_region.shape[:2]
            center_pixel = img_region[center_y // 2, center_x // 2]
            
            # Convert BGR to RGB for comparison
            detected_color = (center_pixel[2], center_pixel[1], center_pixel[0])
            
            # Debug output - show actual vs target colors
            print(f"  🎯 Target color: RGB{target_color}")
            print(f"  👁️  Detected color: RGB{detected_color}")
            
            # Calculate differences for debugging - convert to int to avoid overflow warnings
            r_diff = abs(int(detected_color[0]) - int(target_color[0]))
            g_diff = abs(int(detected_color[1]) - int(target_color[1]))
            b_diff = abs(int(detected_color[2]) - int(target_color[2]))
            max_diff = max(r_diff, g_diff, b_diff)
            print(f"  📊 Color differences: R={r_diff}, G={g_diff}, B={b_diff} (max={max_diff})")
            
            # Check color similarity based on comparator
            if condition.comparator == 'equals':
                # Even with 'equals', use a small tolerance of 3 to account for minor screen variations
                small_tolerance = 3
                match = self._color_similar(detected_color, target_color, small_tolerance)
                print(f"  🔍 Exact match (with small tolerance {small_tolerance}): {'✅ YES' if match else '❌ NO'}")
                if not match and max_diff <= 5:
                    print(f"  💡 Very close match! Consider using 'similar' with tolerance={max_diff+2}")
                return match
            elif condition.comparator == 'similar':
                match = self._color_similar(detected_color, target_color, condition.tolerance)
                print(f"  🔍 Similar match (tolerance {condition.tolerance}): {'✅ YES' if match else '❌ NO'}")
                if not match:
                    suggested_tolerance = max_diff + 5
                    print(f"  💡 Suggested tolerance: {suggested_tolerance}")
                return match
            else:
                # For color detection, treat 'contains' as 'similar'
                match = self._color_similar(detected_color, target_color, condition.tolerance)
                print(f"  🔍 Contains/Similar match (tolerance {condition.tolerance}): {'✅ YES' if match else '❌ NO'}")
                return match
    
    def _color_exists_in_region(self, img_region: np.ndarray, target_color: Tuple[int, int, int], tolerance: int, comparator: str) -> bool:
        """
        Check if a target color exists anywhere in the image region.
        
        Args:
            img_region: Image region to search
            target_color: RGB color to find
            tolerance: Color matching tolerance
            comparator: Comparison method ('equals', 'similar', 'contains')
            
        Returns:
            True if color is found in the region, False otherwise
        """
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_region, cv2.COLOR_BGR2RGB)
        
        if comparator == 'equals':
            # Check for exact color match
            mask = np.all(img_rgb == target_color, axis=2)
            found = np.any(mask)
        else:
            # Check for similar colors within tolerance
            # Calculate color distance for each pixel
            color_diff = np.sqrt(np.sum((img_rgb.astype(float) - np.array(target_color)) ** 2, axis=2))
            found = np.any(color_diff <= tolerance)
        
        pixels_found = np.sum(mask if comparator == 'equals' else color_diff <= tolerance)
        total_pixels = img_region.shape[0] * img_region.shape[1]
        
        print(f"  📊 Found {pixels_found}/{total_pixels} matching pixels")
        print(f"  🔍 Color {'✅ FOUND' if found else '❌ NOT FOUND'} in area")
        
        return found
    
    def detect_text(self, condition: Condition) -> bool:
        """
        Detect if specific text is present at the given position using OCR.
        
        Args:
            condition: Condition object containing text detection parameters
            
        Returns:
            True if text matches based on comparator, False otherwise
        """
        if condition.type != 'text':
            raise ValueError("Condition type must be 'text' for text detection")
        
        if not isinstance(condition.value, str):
            raise ValueError("Text value must be a string")
        
        # Capture region for text detection
        if len(condition.position) == 4:
            # Area selection: use the exact area
            x1, y1, x2, y2 = condition.position
            img_region = self.capture_screen_region(condition.position)
            print(f"  🔍 Scanning text area {condition.position} - size: {x2-x1}x{y2-y1} pixels")
        else:
            # Point selection: capture larger region for text detection (OCR needs more context)
            img_region = self.capture_screen_region(condition.position, region_size=200)
            print(f"  🔍 Scanning text around point {condition.position} - 200x200 pixel area")
        
        target_text = condition.value.strip()
        print(f"  🎯 Target text: '{target_text}'")
        
        try:
            # Enhanced preprocessing pipeline for better OCR
            
            # 1. Convert to grayscale
            gray = cv2.cvtColor(img_region, cv2.COLOR_BGR2GRAY)
            
            # 2. Apply thresholding to make text more distinct
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # 3. Perform OCR on both the grayscale and binary images
            config = '--psm 6 --oem 3'  # Page segmentation mode 6: Assume a single uniform block of text
            detected_text_gray = pytesseract.image_to_string(gray, config=config).strip()
            detected_text_binary = pytesseract.image_to_string(binary, config=config).strip()
            
            # Debug output for both processing methods
            print(f"  👁️  OCR result (gray): '{detected_text_gray}'")
            print(f"  👁️  OCR result (binary): '{detected_text_binary}'")
            
            # 4. Combine results - use whichever one found text
            detected_text = detected_text_gray if detected_text_gray else detected_text_binary
            
            # Try additional OCR mode for small text
            if not detected_text:
                print("  🔄 Trying alternative OCR mode for small text...")
                detected_text = pytesseract.image_to_string(gray, config='--psm 7 --oem 3').strip()
                print(f"  👁️  OCR result (psm 7): '{detected_text}'")
            
            # Try one more OCR mode for sparse text
            if not detected_text:
                print("  🔄 Trying alternative OCR mode for sparse text...")
                detected_text = pytesseract.image_to_string(gray, config='--psm 11 --oem 3').strip()
                print(f"  👁️  OCR result (psm 11): '{detected_text}'")
            
            print(f"  📏 Text length: Target={len(target_text)}, Detected={len(detected_text)}")
            
            # Check text match based on comparator
            result = False
            if condition.comparator == 'equals':
                result = detected_text.lower() == target_text.lower()
                print(f"  🔍 Exact match: {'✅ YES' if result else '❌ NO'}")
            elif condition.comparator == 'contains':
                result = target_text.lower() in detected_text.lower()
                print(f"  🔍 Contains match: {'✅ YES' if result else '❌ NO'}")
            elif condition.comparator == 'similar':
                result = self._text_similar(detected_text, target_text)
                print(f"  🔍 Similar match: {'✅ YES' if result else '❌ NO'}")
                
            return result
            
        except Exception as e:
            print(f"  ❌ OCR error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return False
    
    def evaluate_condition(self, condition: Condition) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            condition: Condition to evaluate
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            if condition.type == 'color':
                return self.detect_color(condition)
            elif condition.type == 'text':
                return self.detect_text(condition)
            else:
                raise ValueError(f"Unknown condition type: {condition.type}")
        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False
    
    def _color_similar(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], tolerance: int) -> bool:
        """
        Check if two colors are similar within a tolerance.
        
        Args:
            color1: First RGB color tuple
            color2: Second RGB color tuple
            tolerance: Maximum allowed difference per channel
            
        Returns:
            True if colors are similar within tolerance
        """
        # Convert to int to avoid numpy overflow warnings
        r_diff = abs(int(color1[0]) - int(color2[0]))
        g_diff = abs(int(color1[1]) - int(color2[1]))
        b_diff = abs(int(color1[2]) - int(color2[2]))
        
        # Calculate both channel-wise and Euclidean distance
        channel_match = r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance
        
        # Calculate Euclidean distance (sqrt of sum of squared differences)
        euclidean_dist = math.sqrt(r_diff*r_diff + g_diff*g_diff + b_diff*b_diff)
        euclidean_match = euclidean_dist <= (tolerance * 1.5)  # Allow slightly larger Euclidean distance
        
        # Return true if either method indicates a match
        return channel_match or euclidean_match
    
    def _text_similar(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """
        Check if two text strings are similar using improved word and character comparison.
        
        Args:
            text1: First text string
            text2: Second text string
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if texts are similar above threshold
        """
        if not text1 or not text2:
            return False
            
        # Convert to lowercase and remove extra whitespace
        text1_clean = ' '.join(text1.lower().split())
        text2_clean = ' '.join(text2.lower().split())
        
        # Check exact match
        if text1_clean == text2_clean:
            return True
            
        # Check if one text contains the other
        if text1_clean in text2_clean or text2_clean in text1_clean:
            return True
            
        # Calculate similarity based on common words
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        
        # Handle empty strings
        if not words1 or not words2:
            return False
            
        # Calculate Jaccard similarity: intersection over union
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        word_similarity = len(intersection) / len(union) if union else 0
        
        # Also calculate character overlap ratio as backup
        common_chars = sum(1 for c in text1_clean if c in text2_clean)
        max_length = max(len(text1_clean), len(text2_clean))
        char_similarity = common_chars / max_length if max_length else 0
        
        # Use the better of the two scores
        similarity = max(word_similarity, char_similarity)
        print(f"  📊 Text similarity score: {similarity:.2f} (threshold: {threshold})")
        
        return similarity >= threshold
