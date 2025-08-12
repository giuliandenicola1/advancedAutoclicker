"""Logging system for autoclicker - comprehensive logging and error tracking.

Fixes (updated):
 - Robust Windows log directory resolution with parents=True.
 - Fallback chain avoids startup crash when APPDATA points to non-existent (e.g. C:/Users/root).
 - Optional override via ADV_AUTOCLICKER_LOG_DIR environment variable.
"""

from __future__ import annotations

import logging
import datetime
from typing import Optional, List
from pathlib import Path
import threading
import os
import platform


class AutoclickerLogger:
    """Centralized logging system for the autoclicker application."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = self._determine_log_dir(log_dir)

        # File paths
        self.main_log_file = self.log_dir / "autoclicker.log"
        self.error_log_file = self.log_dir / "errors.log"
        self.action_log_file = self.log_dir / "actions.log"

        self.lock = threading.Lock()
        self._last_detection_success: Optional[bool] = None
        self._suppressed_not_detected: int = 0

        self._setup_loggers()
        self.log_info("=== Autoclicker Session Started ===")
        self._start_heartbeat()

    # ---------- log directory resolution ----------
    def _determine_log_dir(self, log_dir_param: str) -> Path:
        env_override = os.environ.get("ADV_AUTOCLICKER_LOG_DIR")
        candidates: List[Path] = []
        if env_override:
            candidates.append(Path(env_override).expanduser())

        if log_dir_param != "logs":
            candidates.append(Path(log_dir_param).expanduser())
        else:
            system = platform.system()
            if system == "Darwin":
                candidates.append(Path.home() / "Library" / "Logs" / "AdvancedAutoclicker")
            elif system == "Windows":
                for var in ("APPDATA", "LOCALAPPDATA", "USERPROFILE"):
                    base = os.environ.get(var)
                    if base:
                        p = Path(base) / "AdvancedAutoclicker" / "logs"
                        if "root" in [part.lower() for part in p.parts] and not p.parent.exists():
                            continue
                        candidates.append(p)
            else:
                candidates.append(Path.home() / ".advanced_autoclicker" / "logs")

        import sys
        exe_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates.append(exe_dir / "logs")
        candidates.append(Path.cwd() / "logs")
        candidates.append(Path.cwd())

        for candidate in candidates:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate
            except Exception:
                continue
        return Path.cwd()

    def _start_heartbeat(self):
        def beat():  # pragma: no cover
            import time
            while True:
                try:
                    self.log_debug("heartbeat", "hb")
                except Exception:
                    pass
                time.sleep(30)
        t = threading.Thread(target=beat, name="log-heartbeat", daemon=True)
        t.start()

    def _setup_loggers(self):
        self.main_logger = logging.getLogger('autoclicker.main')
        self.main_logger.setLevel(logging.DEBUG)
        self.error_logger = logging.getLogger('autoclicker.errors')
        self.error_logger.setLevel(logging.ERROR)
        self.action_logger = logging.getLogger('autoclicker.actions')
        self.action_logger.setLevel(logging.INFO)

        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S')

        main_handler = logging.FileHandler(self.main_log_file, encoding='utf-8')
        main_handler.setFormatter(detailed_formatter)
        main_handler.setLevel(logging.DEBUG)

        error_handler = logging.FileHandler(self.error_log_file, encoding='utf-8')
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)

        action_handler = logging.FileHandler(self.action_log_file, encoding='utf-8')
        action_handler.setFormatter(simple_formatter)
        action_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(detailed_formatter)
        console_handler.setLevel(logging.INFO)

        self.main_logger.addHandler(main_handler)
        self.main_logger.addHandler(console_handler)
        self.error_logger.addHandler(error_handler)
        self.error_logger.addHandler(main_handler)
        self.action_logger.addHandler(action_handler)
        self.action_logger.addHandler(main_handler)

        self.main_logger.propagate = False
        self.error_logger.propagate = False
        self.action_logger.propagate = False

    def log_debug(self, message: str, component: str = "general"):
        with self.lock:
            self.main_logger.debug(f"[{component}] {message}")

    def log_info(self, message: str, component: str = "general"):
        with self.lock:
            self.main_logger.info(f"[{component}] {message}")

    def log_warning(self, message: str, component: str = "general"):
        with self.lock:
            self.main_logger.warning(f"[{component}] {message}")

    def log_error(self, message: str, component: str = "general", exception: Optional[Exception] = None):
        with self.lock:
            error_msg = f"[{component}] {message}"
            if exception:
                error_msg += f" | Exception: {exception}"
            self.error_logger.error(error_msg)
            if exception:
                import traceback
                self.error_logger.error(f"[{component}] Traceback: {traceback.format_exc()}")

    def log_action(self, action: str, details: dict = None, success: bool = True):
        with self.lock:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            message = f"{status} | {action}"
            if details:
                detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
                message += f" | {detail_str}"
            self.action_logger.info(message)

    def log_detection(self, position: tuple, condition_type: str, result: bool, details: dict = None):
        status = "DETECTED" if result else "NOT_DETECTED"
        with self.lock:
            if not result and self._last_detection_success is False:
                self._suppressed_not_detected += 1
                return
            action_details = {"position": position, "type": condition_type, "result": status}
            if details:
                action_details.update(details)
            if result and self._suppressed_not_detected:
                self.main_logger.debug(f"[detection] Suppressed {self._suppressed_not_detected} repeated NOT_DETECTED events")
                self._suppressed_not_detected = 0
            self._last_detection_success = result
        self.log_action("DETECTION", action_details, success=result)

    def log_click(self, position: tuple, click_type: str = "single", success: bool = True):
        self.log_action("MOUSE_CLICK", {"position": position, "click_type": click_type}, success=success)

    def log_monitoring(self, action: str, rule_count: int = 0, success: bool = True):
        details = {"action": action}
        if rule_count > 0:
            details["rules"] = rule_count
        self.log_action("MONITORING", details, success=success)

    def log_rule_match(self, rule_logic: str, condition_count: int, position: tuple):
        self.log_action("RULE_MATCHED", {"logic": rule_logic, "conditions": condition_count, "position": position}, success=True)

    def log_delay_popup(self, action: str, delay_seconds: int = 0, popup_enabled: bool = False):
        details = {"action": action}
        if delay_seconds > 0:
            details["delay"] = f"{delay_seconds}s"
        if popup_enabled:
            details["popup"] = "enabled"
        self.log_action("DELAY_POPUP", details, success=True)

    def get_recent_logs(self, log_type: str = "main", lines: int = 100) -> List[str]:
        log_file_map = {"main": self.main_log_file, "error": self.error_log_file, "action": self.action_log_file}
        log_file = log_file_map.get(log_type, self.main_log_file)
        try:
            if not log_file.exists():
                return []
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
        except Exception as e:
            self.log_error(f"Failed to read log file {log_file}", "logger", e)
            return [f"Error reading log file: {e}"]

    def get_logs_by_type(self, log_type: str, lines: int = 500) -> List[str]:
        return self.get_recent_logs(log_type, lines)

    def get_all_logs(self, lines: int = 500) -> List[str]:
        return self.get_recent_logs("main", lines)

    def clear_all_logs(self):  # compatibility
        self.clear_logs("all")

    def get_log_stats(self) -> dict:
        stats = {}
        log_files = {"main": self.main_log_file, "error": self.error_log_file, "action": self.action_log_file}
        for log_type, log_file in log_files.items():
            try:
                if log_file.exists():
                    stat = log_file.stat()
                    with open(log_file, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    stats[log_type] = {
                        "file": str(log_file),
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / 1024 / 1024, 2),
                        "lines": line_count,
                        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    stats[log_type] = {"file": str(log_file), "exists": False}
            except Exception as e:
                stats[log_type] = {"error": str(e)}
        return stats

    def clear_logs(self, log_type: str = "all"):
        if log_type == "all":
            targets = [self.main_log_file, self.error_log_file, self.action_log_file]
        elif log_type == "main":
            targets = [self.main_log_file]
        elif log_type == "error":
            targets = [self.error_log_file]
        elif log_type == "action":
            targets = [self.action_log_file]
        else:
            targets = []
        for lf in targets:
            try:
                if lf.exists():
                    lf.unlink()
                    self.log_info(f"Cleared log file: {lf.name}", "logger")
            except Exception as e:
                self.log_error(f"Failed to clear log file {lf.name}", "logger", e)

    def export_logs(self, export_path: str, log_type: str = "all") -> bool:
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(exist_ok=True)
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            if log_type == "all":
                mapping = [
                    (self.main_log_file, f"autoclicker_main_{ts}.log"),
                    (self.error_log_file, f"autoclicker_errors_{ts}.log"),
                    (self.action_log_file, f"autoclicker_actions_{ts}.log"),
                ]
            else:
                m = {"main": self.main_log_file, "error": self.error_log_file, "action": self.action_log_file}
                src = m.get(log_type)
                if not src:
                    return False
                mapping = [(src, f"autoclicker_{log_type}_{ts}.log")]
            for src, name in mapping:
                if src.exists():
                    (export_dir / name).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
            self.log_info(f"Exported logs to {export_path}", "logger")
            return True
        except Exception as e:
            self.log_error(f"Failed to export logs to {export_path}", "logger", e)
            return False

    def close(self):
        self.log_info("=== Autoclicker Session Ended ===")
        for logger in [self.main_logger, self.error_logger, self.action_logger]:
            for handler in list(logger.handlers):
                try:
                    handler.close()
                except Exception:
                    pass


_logger_instance: Optional[AutoclickerLogger] = None


def get_logger() -> AutoclickerLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AutoclickerLogger()
    return _logger_instance


def init_logger(log_dir: str = "logs") -> AutoclickerLogger:
    global _logger_instance
    if _logger_instance is not None:
        _logger_instance.close()
    _logger_instance = AutoclickerLogger(log_dir)
    return _logger_instance


def close_logger():
    global _logger_instance
    if _logger_instance is not None:
        _logger_instance.close()
        _logger_instance = None
