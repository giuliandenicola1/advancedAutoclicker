"""Startup diagnostics utilities for the Modern Autoclicker.

Captures environment, platform, packaging (frozen) state, key module
availability, working directories, and resource paths to aid debugging
when running inside a packaged app bundle.
"""

from __future__ import annotations

import os
import sys
import platform
import importlib
from pathlib import Path
from typing import Dict, Any


OPTIONAL_MODULES = [
    "ttkbootstrap",
    "cv2",
    "pyautogui",
    "pytesseract",
    "PIL",
]


def _check_module(name: str) -> str:
    try:
        importlib.import_module(name)
        return "available"
    except Exception as e:  # pragma: no cover - best effort
        return f"missing ({e.__class__.__name__}: {e})"


def gather_startup_diagnostics() -> Dict[str, Any]:
    cwd = os.getcwd()
    frozen = getattr(sys, "frozen", False)
    bundle_dir = Path(sys.executable).parent.parent if frozen else None
    base_path = getattr(sys, "_MEIPASS", None)
    env_subset_keys = ["PATH", "DISPLAY", "PYTHONPATH"]
    env_info = {k: os.environ.get(k) for k in env_subset_keys if k in os.environ}

    module_status = {m: _check_module(m) for m in OPTIONAL_MODULES}

    tcl_library = os.environ.get("TCL_LIBRARY")
    tk_library = os.environ.get("TK_LIBRARY")

    paths_exist = {
        "logs_dir": str(Path("logs").resolve()),
        "has_logs_dir": Path("logs").exists(),
    }

    return {
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "arch": platform.machine(),
        "frozen": frozen,
        "sys_executable": sys.executable,
        "bundle_dir": str(bundle_dir) if bundle_dir else None,
        "meipass": base_path,
        "cwd": cwd,
        "module_status": module_status,
        "env_subset": env_info,
        "tcl_library": tcl_library,
        "tk_library": tk_library,
        "path_entries": sys.path[:10],  # limit length
        "paths_exist": paths_exist,
    }


def log_startup_diagnostics(logger):
    data = gather_startup_diagnostics()
    logger.log_info("Startup diagnostics begin", "diagnostics")
    for key, value in data.items():
        logger.log_info(f"{key}: {value}", "diagnostics")
    logger.log_info("Startup diagnostics end", "diagnostics")


def run_startup_diagnostics(logger):  # public alias
    log_startup_diagnostics(logger)
