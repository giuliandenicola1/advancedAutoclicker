#!/usr/bin/env python3
"""
Autoclicker main entry point with AC-3 delay/popup functionality
"""
import sys
from ui import AutoclickerUI
from permission_preflight import run_permission_preflight


def main():
    """Main entry point for the autoclicker application"""
    try:
        print("Starting Autoclicker with AC-3 Delay/Popup functionality...")
        # Trigger macOS permission prompts early (no-op on other platforms)
        run_permission_preflight()
        app = AutoclickerUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
