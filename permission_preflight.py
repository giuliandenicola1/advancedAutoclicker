"""Permission preflight routines for macOS.

Goal: trigger ONLY the Screen Recording prompt early (by taking a tiny
screenshot) while avoiding an early Accessibility (control) prompt unless
really needed. Prompting both simultaneously has been observed to cause
confusion and (on some systems) a repeated Screen Recording prompt loop
when the app is not yet moved to /Applications or remains unsigned.

Behavior:
 - Runs once per process (idempotent).
 - If env ACLICKER_PREFLIGHT=off -> fully skipped.
 - If env ACLICKER_PREFLIGHT=light (default) -> only tiny screenshot.
 - If env ACLICKER_PREFLIGHT=full  -> screenshot + safe corner click (old behavior).

Why defer Accessibility? Users often grant Screen Recording first; clicking
before Accessibility is granted can yield repeated prompts or failures that
look like Screen Recording issues. We'll request control permission only
when an actual automated click is attempted (later in workflow) rather than
at cold start.
"""
from __future__ import annotations

import sys
import os
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

    # Respect override / disable flag.
    mode = os.environ.get("ACLICKER_PREFLIGHT", "light").lower().strip()
    if mode == "off":
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
        # Always attempt tiny screenshot (Screen Recording prompt)
        try:
            pyautogui.screenshot(region=(0, 0, min(8, width), min(8, height)))
        except Exception as shot_err:
            if logger and hasattr(logger, "log_error"):
                logger.log_error(f"Screenshot preflight error: {shot_err}", "preflight", shot_err)
            else:
                print(f"[preflight] Screenshot error: {shot_err}")

        did_click = False
        if mode == "full":
            # OPTIONAL accessibility trigger only in 'full' mode
            safe_x = 1 if width > 2 else 0
            safe_y = 1 if height > 2 else 0
            try:
                old_pause = pyautogui.PAUSE
                pyautogui.PAUSE = 0.05
                pyautogui.moveTo(safe_x, safe_y, duration=0.05)
                pyautogui.click(button="left")
                pyautogui.PAUSE = old_pause
                did_click = True
            except Exception as click_err:
                if logger and hasattr(logger, "log_error"):
                    logger.log_error(f"Accessibility (click) preflight error: {click_err}", "preflight", click_err)
                else:
                    print(f"[preflight] Click error: {click_err}")

        guidance = [
            "Grant Screen Recording permission if prompted.",
            "Move the app to /Applications before granting permissions (prevents repeat prompts).",
            "After granting restart the app if captures are still black.",
        ]
        if not did_click:
            guidance.append("Accessibility permission will be requested later when an actual automated click occurs.")
        else:
            guidance.append("Accessibility permission may also have been requested (full mode).")
        guidance_text = " ".join(guidance)
        if logger and hasattr(logger, "log_info"):
            logger.log_info(guidance_text, "preflight")
        else:
            print(f"[preflight] {guidance_text}")
    except Exception as e:  # pragma: no cover - broad safeguard
        if logger and hasattr(logger, "log_error"):
            logger.log_error(f"Unexpected preflight error: {e}", "preflight", e)
        else:
            print(f"[preflight] Unexpected error: {e}")
