"""Entry point for the modern (new_ui) based Advanced Autoclicker application.

Adds robust startup logging and crash reporting so packaged builds
surface errors in logs and optionally a message box.
"""

from new_ui import ModernAutoclickerUI
from logger import get_logger
from permission_preflight import run_permission_preflight
import traceback
import os
import sys


def main():
    logger = get_logger()
    logger.log_info("=== Launching Advanced Autoclicker (modern UI) ===", "startup")
    logger.log_info(f"Executable: {sys.executable}", "startup")
    logger.log_info(f"Working Dir: {os.getcwd()}", "startup")
    logger.log_info(f"Frozen: {getattr(sys, 'frozen', False)}", "startup")
    try:
        # Trigger macOS permission prompts early (no-op on other platforms)
        run_permission_preflight(logger)
        app = ModernAutoclickerUI()
        app.run()
    except Exception as e:  # capture and log any startup crash
        tb = traceback.format_exc()
        logger.log_error(f"Fatal startup error: {e}", "startup", e)
        print("Startup failed:\n", tb)
        # Attempt GUI notification last resort
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Advanced Autoclicker Crash",
                f"Startup failed: {e}\nSee logs for details."
            )
            root.destroy()
        except Exception:
            pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
