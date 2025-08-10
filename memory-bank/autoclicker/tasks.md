# Task Breakdown: Autoclicker

---

## AC-1: UI for Position & Rule Selection
- **Description:** Build a simple UI to let the user select a screen position and define detection rules (color, text, etc.).
- **Acceptance Criteria:**
  - User can select a pixel on the screen.
  - User can add/edit/remove conditions (color, text, etc.).
  - User can configure logic (any, all, n-of).
- **Effort:** L
- **Files/Modules:** ui.py, config.py

---

## AC-2: Screen Monitoring & Detection Engine
- **Description:** Implement background monitoring of the selected position(s) and evaluate conditions using color detection and OCR.
- **Acceptance Criteria:**
  - Monitors screen at user-selected position(s).
  - Detects color and/or text as configured.
  - Supports multiple conditions and logic rules.
- **Effort:** L
- **Files/Modules:** monitor.py, detection.py

---

## AC-3: Delay/Popup & User Intervention
- **Description:** Add a configurable delay and/or popup before simulating a click, allowing the user to cancel.
- **Acceptance Criteria:**
  - User can set delay (0, 5s, 10s, etc.).
  - Popup appears (if enabled) with cancel option.
- **Effort:** M
- **Files/Modules:** ui.py, main.py

---

## AC-4: Mouse Click Simulation
- **Description:** Simulate a mouse click at the detected position when conditions are met and delay (if any) has elapsed.
- **Acceptance Criteria:**
  - Mouse click is performed at the correct position.
  - Works reliably on macOS (and cross-platform if possible).
- **Effort:** M
- **Files/Modules:** clicker.py

---

## AC-5: Logging & Error Handling
- **Description:** Add logging for actions and errors for debugging and user feedback.
- **Acceptance Criteria:**
  - All actions and errors are logged to a file.
  - User can view logs from the UI.
- **Effort:** S
- **Files/Modules:** logger.py, ui.py
