"""
Detection engine for autoclicker - handles color and text detection at screen positions.
"""

import cv2
import numpy as np
import pytesseract
import pyautogui
import math
import difflib
import os
import time
import re
import string
from pathlib import Path
from typing import Tuple, Union, List, Dict
from config import Condition


class DetectionEngine:
    """Handles detection of colors and text at specific screen positions"""
    
    def __init__(self):
        # Disable pyautogui failsafe for smoother operation
        pyautogui.FAILSAFE = False
        
        # Verify Tesseract OCR is available
        try:
            # Allow explicit override via environment variable if user installed tesseract in a non-standard path
            tess_cmd = os.environ.get("TESSERACT_CMD")
            if tess_cmd:
                pytesseract.pytesseract.tesseract_cmd = tess_cmd
            pytesseract.get_tesseract_version()
            print("✅ Tesseract OCR detected")
        except Exception as e:
            print(f"⚠️ Warning: Tesseract OCR may not be properly installed: {e}")
            print("Text detection features may not work correctly.")
            print("  👉 On macOS: brew install tesseract")
            print("  👉 If installed but not found: export TESSERACT_CMD=\"/opt/homebrew/bin/tesseract\"")
        
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
            start_time = time.time()
            preprocessed_variants = self._preprocess_for_ocr(img_region)

            # -------- FAST PATH --------
            fast_mode = os.environ.get('ADV_OCR_FAST', '1') != '0'
            if fast_mode:
                gray = preprocessed_variants.get('gray')
                # Quick token fetch via image_to_data
                tokens_fast = self._ocr_tokens(gray)
                if tokens_fast:
                    norm_tokens_fast = [t.lower().strip('.,:;') for t in tokens_fast]
                    tl = target_text.lower()
                    if ((condition.comparator == 'equals' and tl in norm_tokens_fast) or
                        (condition.comparator == 'contains' and any(tl in t for t in norm_tokens_fast)) or
                        (condition.comparator == 'similar' and any(self._text_similar(t, target_text) for t in norm_tokens_fast))):
                        elapsed = (time.time() - start_time) * 1000
                        print(f"  ⚡ FAST token match in {elapsed:.1f}ms")
                        return True
                # Single quick full text pass
                try:
                    quick_text = pytesseract.image_to_string(gray, config='--psm 6 --oem 3').strip()
                except Exception:
                    quick_text = ''
                if quick_text:
                    ql = quick_text.lower()
                    tl = target_text.lower()
                    if ((condition.comparator == 'equals' and ql == tl) or
                        (condition.comparator == 'contains' and tl in ql) or
                        (condition.comparator == 'similar' and self._text_similar(quick_text, target_text))):
                        elapsed = (time.time() - start_time) * 1000
                        print(f"  ⚡ FAST full-text match in {elapsed:.1f}ms -> '{quick_text[:60].replace('\n',' / ')}'")
                        return True
                # Allow disabling exhaustive pass
                if os.environ.get('ADV_OCR_FULL_FALLBACK','1') == '0':
                    elapsed = (time.time() - start_time) * 1000
                    print(f"  🛑 Fast mode no match (fallback disabled) elapsed {elapsed:.1f}ms")
                    return False

            # Run multiple OCR strategies
            ocr_attempts: List[Dict[str, str]] = []
            base_psm_sequence = [6, 7, 11, 3, 13]  # Prioritized PSM modes
            whitelist = self._derive_whitelist(target_text)

            # Allow customization via environment vars
            env_psm = os.environ.get('ADV_OCR_PSMS')
            if env_psm:
                try:
                    seq = [int(x) for x in env_psm.split(',') if x.strip().isdigit()]
                    if seq:
                        base_psm_sequence = seq
                        print(f"  [OCR] Using custom PSM sequence {base_psm_sequence}")
                except Exception:
                    pass
            env_variants = os.environ.get('ADV_OCR_VARIANTS')
            variant_items = preprocessed_variants.items()
            if env_variants:
                requested = [v.strip() for v in env_variants.split(',')]
                filtered = [(k, preprocessed_variants[k]) for k in requested if k in preprocessed_variants]
                if filtered:
                    variant_items = filtered
                    print(f"  [OCR] Using custom variants {', '.join(k for k,_ in filtered)}")

            for variant_name, variant_img in variant_items:
                for psm in base_psm_sequence:
                    config_parts = [f"--psm {psm}", "--oem 3"]
                    if whitelist:
                        config_parts.append(f"-c tessedit_char_whitelist={whitelist}")
                    config = " ".join(config_parts)
                    try:
                        text = pytesseract.image_to_string(variant_img, config=config).strip()
                    except Exception as ocr_e:
                        print(f"  ⚠️ OCR failure on {variant_name} psm={psm}: {ocr_e}")
                        text = ""
                    if text:
                        ocr_attempts.append({
                            'variant': variant_name,
                            'psm': str(psm),
                            'text': text
                        })
                        print(f"  👁  [{variant_name} | psm {psm}] -> '{text[:120].replace('\n',' / ')}{'...' if len(text)>120 else ''}'")
                        # Quick token extraction from this attempt for early exit
                        quick_tokens = self._extract_tokens_from_text(text)
                        if target_text.lower() in [t.lower() for t in quick_tokens]:
                            elapsed = (time.time()-start_time)*1000
                            print(f"  ✅ Early token match '{target_text}' in variant={variant_name} psm={psm} ({elapsed:.1f}ms)")
                            return True
                        # Short-circuit if we already have an exact match
                        if text.lower() == target_text.lower():
                            elapsed = (time.time()-start_time)*1000
                            print(f"  ✅ Early exact match; stopping further OCR attempts ({elapsed:.1f}ms)")
                            return True

            # Aggregate all detected texts
            combined_text = " | ".join([a['text'] for a in ocr_attempts])
            print(f"  [OCR] Combined text length={len(combined_text)}")

            # Token level evaluation using image_to_data for highest recall
            tokens = self._ocr_tokens(preprocessed_variants.get('enhanced', list(preprocessed_variants.values())[0]))
            if tokens:
                print(f"  🧩 OCR tokens ({len(tokens)}): {tokens[:25]}{'...' if len(tokens)>25 else ''}")
                # Early token direct hit
                if target_text.lower() in [t.lower().strip('.,:;') for t in tokens]:
                    print("  ✅ Direct token list match")
                    return True

            # Evaluate match conditions
            target_lower = target_text.lower()
            detected_any = False

            # Helper closure for comparators
            def eval_match(text: str) -> bool:
                if condition.comparator == 'equals':
                    return text.lower() == target_lower
                elif condition.comparator == 'contains':
                    return target_lower in text.lower()
                elif condition.comparator == 'similar':
                    return self._text_similar(text, target_text)
                return False

            # Build candidate lines (flatten all attempt texts into individual lines, cleaned)
            candidate_lines: List[str] = []
            for attempt in ocr_attempts:
                for line in attempt['text'].splitlines():
                    norm_line = self._normalize_ocr_line(line)
                    if norm_line:
                        candidate_lines.append(norm_line)

            if candidate_lines:
                best_ratio = 0.0
                best_line = None
                for line in candidate_lines:
                    ratio = difflib.SequenceMatcher(None, line.lower(), target_lower).ratio()
                    if ratio > best_ratio:
                        best_ratio, best_line = ratio, line
                    if eval_match(line):
                        elapsed = (time.time()-start_time)*1000
                        print(f"  ✅ Line match: '{line}' ({elapsed:.1f}ms)")
                        return True
                print(f"  [OCR] Best line candidate='{best_line}' ratio={best_ratio:.2f}")
                if condition.comparator in ('similar','contains') and best_ratio >= 0.85:
                    print("  ✅ Accepted via best line similarity >=0.85")
                    return True

            # 1. Check full attempt strings
            for attempt in ocr_attempts:
                if eval_match(attempt['text']):
                    elapsed = (time.time()-start_time)*1000
                    print(f"  ✅ Match via variant={attempt['variant']} psm={attempt['psm']} ({elapsed:.1f}ms)")
                    return True

            # 2. Check combined text
            if combined_text and eval_match(combined_text):
                elapsed = (time.time()-start_time)*1000
                print(f"  ✅ Match in combined OCR text ({elapsed:.1f}ms)")
                return True

            # 3. Check tokens individually and joined
            if tokens:
                for tok in tokens:
                    if eval_match(tok):
                        elapsed = (time.time()-start_time)*1000
                        print(f"  ✅ Match via token '{tok}' ({elapsed:.1f}ms)")
                        return True
                joined_tokens = " ".join(tokens)
                if eval_match(joined_tokens):
                    elapsed = (time.time()-start_time)*1000
                    print(f"  ✅ Match via joined tokens ({elapsed:.1f}ms)")
                    return True

            # 4. Fuzzy matching across attempts (SequenceMatcher ratio)
            for attempt in ocr_attempts:
                ratio = difflib.SequenceMatcher(None, attempt['text'].lower(), target_lower).ratio()
                print(f"  [OCR] Attempt fuzzy ratio ({attempt['variant']}|psm {attempt['psm']}): {ratio:.2f}")
                if condition.comparator in ('similar', 'contains') and ratio >= 0.8:
                    elapsed = (time.time()-start_time)*1000
                    print(f"  ✅ Accepted via fuzzy ratio >= 0.8 ({elapsed:.1f}ms)")
                    return True

            # Export debug images if nothing found
            if not detected_any:
                self._export_ocr_debug_images(preprocessed_variants, condition, target_text)
                elapsed = (time.time()-start_time)*1000
                print(f"  � Exported OCR debug images for inspection. Total {elapsed:.1f}ms")
            return False

        except Exception as e:
            print(f"  ❌ OCR error: {e}")
            import traceback
            traceback.print_exc()
            return False

    # --------------- OCR helper methods ---------------
    def _preprocess_for_ocr(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        """Generate multiple preprocessed variants to maximize OCR success."""
        variants: Dict[str, np.ndarray] = {}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        variants['gray'] = gray

        # Adaptive threshold (handles varying backgrounds)
        adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 31, 9)
        variants['adaptive'] = adapt

        # OTSU (normal + inverted)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants['otsu'] = otsu
        variants['otsu_inv'] = cv2.bitwise_not(otsu)

        # Morphological enhancement
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(otsu, kernel, iterations=1)
        eroded = cv2.erode(otsu, kernel, iterations=1)
        variants['dilated'] = dilated
        variants['eroded'] = eroded

        # Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(gray)
        _, cl_bin = cv2.threshold(cl, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants['clahe'] = cl
        variants['clahe_bin'] = cl_bin

        # Enlarged (upsample) for small fonts
        h, w = gray.shape[:2]
        if max(h, w) < 200:
            scale = 2
            enlarged = cv2.resize(gray, (w*scale, h*scale), interpolation=cv2.INTER_CUBIC)
            variants['enlarged'] = enlarged

        # Enhanced variant (best guess for token parsing)
        variants['enhanced'] = variants.get('adaptive', gray)
        return variants

    def _ocr_tokens(self, img: np.ndarray) -> List[str]:
        """Extract individual word tokens using image_to_data for more granular matching."""
        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config='--psm 6 --oem 3')
            words = []
            for i, txt in enumerate(data.get('text', [])):
                if txt and txt.strip():
                    words.append(txt.strip())
            return words
        except Exception as e:
            print(f"  ⚠️ Token OCR failure: {e}")
            return []

    def _derive_whitelist(self, target: str) -> str:
        """Attempt to derive a whitelist of characters if target text is restrictive (digits, hex, etc.)."""
        if not target:
            return ""
        unique = set(target)
        # If alphanumeric set is small (<15) we can whitelist to reduce noise
        if len(unique) < 15:
            allowed = ''.join(sorted(ch for ch in unique if ch.isalnum() or ch in '-_:+/'))
            return allowed
        return ""

    # --- NEW helpers for line normalization & quick token extraction ---
    def _normalize_ocr_line(self, line: str) -> str:
        """Reduce noise in a single OCR line (strip artifacts, collapse repeats)."""
        if not line:
            return ""
        # Remove zero-width / unusual quotes, unify quotes
        line = line.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
        # Strip non-printable
        line = ''.join(ch for ch in line if ch in string.printable)
        # Collapse 3+ repeated same letters that often arise from anti-aliasing (e.g. tttteeee)
        line = re.sub(r'(\w)\1{2,}', r'\1\1', line)
        # Remove isolated punctuation clusters
        line = re.sub(r'[^A-Za-z0-9]+', ' ', line)
        line = ' '.join(line.split())
        return line.strip()

    def _extract_tokens_from_text(self, text: str) -> List[str]:
        """Fast token extraction from a raw OCR block used for early exits."""
        if not text:
            return []
        # Split on non-alphanumeric boundaries, filter short noise (<2 chars unless digit)
        raw = re.split(r'[^A-Za-z0-9]+', text)
        tokens = [t for t in raw if (len(t) > 1 or t.isdigit())]
        # De-duplicate preserving order
        seen = set()
        ordered: List[str] = []
        for t in tokens:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                ordered.append(t)
        return ordered

    def _export_ocr_debug_images(self, variants: Dict[str, np.ndarray], condition: Condition, target_text: str):
        """Save variant images to a debug folder for manual inspection."""
        try:
            debug_root = Path('logs') / 'ocr_debug'
            debug_root.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            base = f"ocr_{timestamp}_pos_{'_'.join(map(str, condition.position))}_target_{self._slugify(target_text)[:30]}"
            for name, img in variants.items():
                out_path = debug_root / f"{base}_{name}.png"
                try:
                    if len(img.shape) == 2:
                        cv2.imwrite(str(out_path), img)
                    else:
                        cv2.imwrite(str(out_path), cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                except Exception as inner_e:
                    print(f"  ⚠️ Failed to save debug image {name}: {inner_e}")
        except Exception as e:
            print(f"  ⚠️ Failed exporting OCR debug images: {e}")

    def _slugify(self, text: str) -> str:
        return ''.join(ch if ch.isalnum() else '_' for ch in text)
    
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
        """Heuristic similarity between OCR text and target.

        Steps:
          1. Normalize whitespace & case.
          2. Exact & containment checks.
          3. Word-level Jaccard similarity.
          4. Character overlap ratio.
          5. Return True if max(word, char) >= threshold (env override ADV_OCR_SIM_THRESHOLD).
        """
        # Dynamic threshold override
        env_thr = os.environ.get('ADV_OCR_SIM_THRESHOLD')
        if env_thr:
            try:
                threshold = float(env_thr)
            except ValueError:
                pass

        if not text1 or not text2:
            return False

        text1_clean = ' '.join(text1.lower().split())
        text2_clean = ' '.join(text2.lower().split())

        if not text1_clean or not text2_clean:
            return False

        if text1_clean == text2_clean:
            return True
        if text1_clean in text2_clean or text2_clean in text1_clean:
            return True

        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        if not words1 or not words2:
            return False

        intersection = words1 & words2
        union = words1 | words2
        word_similarity = len(intersection) / len(union) if union else 0.0

        common_chars = sum(1 for c in text1_clean if c in text2_clean)
        max_length = max(len(text1_clean), len(text2_clean))
        char_similarity = common_chars / max_length if max_length else 0.0

        similarity = max(word_similarity, char_similarity)
        print(f"  📊 Text similarity score: {similarity:.2f} (threshold: {threshold})")
        return similarity >= threshold
