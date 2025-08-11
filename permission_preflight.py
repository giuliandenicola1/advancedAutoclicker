"""Permission preflight routines for macOS.

This module attempts a minimal screen capture and a harmless corner click
early at startup so macOS will immediately prompt the user for the required
Screen Recording and Accessibility permissions (instead of later during a
critical action). The operations are intentionally tiny and target an
off-screen-impact area (a screen corner) to avoid unwanted side‑effects.

Safe to call multiple times; it will only execute once per process.
"""
from __future__ import annotations

import sys
import threading
from typing import Optional

_ran_lock = threading.Lock()
_ran: bool = False


def run_permission_preflight(logger: Optional[object] = None) -> None:
    """Attempt to trigger macOS permission prompts (idempotent).

    On macOS, the first call to take a screenshot triggers the Screen
    Recording permission prompt (if not previously granted) and the first
    programmatic mouse control triggers the Accessibility permission prompt.

    We perform both actions early so the user can grant them before using
    the main UI. On other platforms this is a no‑op.
    """
    global _ran
    with _ran_lock:
        if _ran:
            return
        _ran = True

    if sys.platform != "darwin":  # Only relevant on macOS
        return

    # Lazy import so non-mac platforms aren't burdened.
    try:
        import pyautogui  # type: ignore
    except Exception as e:  # pragma: no cover - import failure path
        if logger and hasattr(logger, "log_error"):
            logger.log_error(f"Preflight skipped (pyautogui import failed): {e}", "preflight", e)
        else:
            print(f"[preflight] Skipped pyautogui import failure: {e}")
        return

    try:
        width, height = pyautogui.size()
        # Choose a safe corner (top-left). We'll click at (1,1) to avoid FailSafe (0,0).
        safe_x = 1 if width > 2 else 0
        safe_y = 1 if height > 2 else 0

        if logger and hasattr(logger, "log_info"):
            logger.log_info(
                f"Running macOS permission preflight (screen {width}x{height}, point=({safe_x},{safe_y}))",
                "preflight",
            )
        else:
            print(f"[preflight] Triggering macOS permission prompts (screen {width}x{height})")

        # 1. Screen recording permission trigger: tiny screenshot.
        try:
            pyautogui.screenshot(region=(0, 0, min(10, width), min(10, height)))
        except Exception as shot_err:
            if logger and hasattr(logger, "log_error"):
                logger.log_error(f"Screenshot preflight error: {shot_err}", "preflight", shot_err)
            else:
                print(f"[preflight] Screenshot error: {shot_err}")

        # 2. Accessibility permission trigger: move & click in safe corner.
        try:
            # Temporarily relax pause to be quick but not instant.
            old_pause = pyautogui.PAUSE
            pyautogui.PAUSE = 0.05
            pyautogui.moveTo(safe_x, safe_y, duration=0.05)
            # Use a very short mouseDown/up rather than full click to minimize visual disturbance.
            pyautogui.mouseDown(button="left")
            pyautogui.mouseUp(button="left")
            pyautogui.PAUSE = old_pause
        except Exception as click_err:
            if logger and hasattr(logger, "log_error"):
                logger.log_error(f"Click preflight error: {click_err}", "preflight", click_err)
            else:
                print(f"[preflight] Click error: {click_err}")

        guidance = (
            "If macOS prompts for permissions, please grant: System Settings > "
            "Privacy & Security > (Screen Recording, Accessibility) for this app. "
            "Restart the app after granting if clicks or captures still fail."
        )
        if logger and hasattr(logger, "log_info"):
            logger.log_info(guidance, "preflight")
        else:
            print(f"[preflight] {guidance}")
    except Exception as e:  # pragma: no cover - broad safeguard
        if logger and hasattr(logger, "log_error"):
            logger.log_error(f"Unexpected preflight error: {e}", "preflight", e)
        else:
            print(f"[preflight] Unexpected error: {e}")
