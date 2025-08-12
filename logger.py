"""
Logging system for autoclicker - handles comprehensive logging and error tracking.
"""

import logging
import datetime
from typing import Optional, List
from pathlib import Path
import threading
import os
import platform


class AutoclickerLogger:
    """Centralized logging system for the autoclicker application"""

    def __init__(self, log_dir: str = "logs"):
        """Initialize the logging system.

        Args:
            log_dir: Directory to store log files
        """
        # Resolve log directory
        if log_dir == "logs":
            system = platform.system()
            if system == "Darwin":
                base = Path.home() / "Library" / "Logs" / "AdvancedAutoclicker"
            elif system == "Windows":
                # Prefer APPDATA, fallback to LOCALAPPDATA, then home
                appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
                base = Path(appdata) / "AdvancedAutoclicker" / "logs"
            else:
                base = Path.home() / ".advanced_autoclicker" / "logs"
            self.log_dir = base
        else:
            self.log_dir = Path(log_dir)
        # Ensure directory tree; fallback locally if creation fails (e.g., permission/path issues)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            fallback = Path.cwd() / "logs"
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                self.log_dir = fallback
                # can't log yet; will log once logger initialized
            except Exception:
                # As last resort use current working directory without subfolder
                self.log_dir = Path.cwd()

        # File paths
        self.main_log_file = self.log_dir / "autoclicker.log"
        self.error_log_file = self.log_dir / "errors.log"
        self.action_log_file = self.log_dir / "actions.log"

        # Synchronization
        self.lock = threading.Lock()

        # Detection suppression state
        self._last_detection_success: Optional[bool] = None
        self._suppressed_not_detected: int = 0

        # Configure loggers and start session
        self._setup_loggers()
        self.log_info("=== Autoclicker Session Started ===")
        self._start_heartbeat()

    def _start_heartbeat(self):
        """Start a background thread to write heartbeat lines so we see if UI loop stalls."""
        def beat():  # pragma: no cover - timing thread
            while True:
                try:
                    self.log_debug("heartbeat", "hb")
                except Exception:
                    pass
                import time
                time.sleep(30)
        t = threading.Thread(target=beat, name="log-heartbeat", daemon=True)
        t.start()
        
    def _setup_loggers(self):
        """Setup different loggers for different purposes"""
        
        # Main logger
        self.main_logger = logging.getLogger('autoclicker.main')
        self.main_logger.setLevel(logging.DEBUG)
        
        # Error logger
        self.error_logger = logging.getLogger('autoclicker.errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Action logger
        self.action_logger = logging.getLogger('autoclicker.actions')
        self.action_logger.setLevel(logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handlers
        main_handler = logging.FileHandler(self.main_log_file, encoding='utf-8')
        main_handler.setFormatter(detailed_formatter)
        main_handler.setLevel(logging.DEBUG)
        
        error_handler = logging.FileHandler(self.error_log_file, encoding='utf-8')
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        
        action_handler = logging.FileHandler(self.action_log_file, encoding='utf-8')
        action_handler.setFormatter(simple_formatter)
        action_handler.setLevel(logging.INFO)
        
        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(detailed_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Add handlers to loggers
        self.main_logger.addHandler(main_handler)
        self.main_logger.addHandler(console_handler)
        
        self.error_logger.addHandler(error_handler)
        self.error_logger.addHandler(main_handler)  # Errors also go to main log
        
        self.action_logger.addHandler(action_handler)
        self.action_logger.addHandler(main_handler)  # Actions also go to main log
        
        # Prevent duplicate logs
        self.main_logger.propagate = False
        self.error_logger.propagate = False
        self.action_logger.propagate = False
    
    def log_debug(self, message: str, component: str = "general"):
        """Log debug information"""
        with self.lock:
            self.main_logger.debug(f"[{component}] {message}")
    
    def log_info(self, message: str, component: str = "general"):
        """Log general information"""
        with self.lock:
            self.main_logger.info(f"[{component}] {message}")
    
    def log_warning(self, message: str, component: str = "general"):
        """Log warning messages"""
        with self.lock:
            self.main_logger.warning(f"[{component}] {message}")
    
    def log_error(self, message: str, component: str = "general", exception: Optional[Exception] = None):
        """Log error messages"""
        with self.lock:
            error_msg = f"[{component}] {message}"
            if exception:
                error_msg += f" | Exception: {str(exception)}"
            
            self.error_logger.error(error_msg)
            
            # Log exception traceback if available
            if exception:
                import traceback
                self.error_logger.error(f"[{component}] Traceback: {traceback.format_exc()}")
    
    def log_action(self, action: str, details: dict = None, success: bool = True):
        """Log user actions and system events"""
        with self.lock:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            message = f"{status} | {action}"
            
            if details:
                detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
                message += f" | {detail_str}"
            
            self.action_logger.info(message)
    
    def log_detection(self, position: tuple, condition_type: str, result: bool, details: dict = None):
        """Log detection events"""
        status = "DETECTED" if result else "NOT_DETECTED"

        # Suppress consecutive NOT_DETECTED entries to avoid console flooding
        # Only the first NOT_DETECTED after a DETECTED (or start) is shown until a DETECTED happens.
        with self.lock:
            if not result and self._last_detection_success is False:
                self._suppressed_not_detected += 1
                return

            action_details = {
                "position": position,
                "type": condition_type,
                "result": status
            }
            if details:
                action_details.update(details)

            # If we are about to log a DETECTED and had suppressed prior NOT_DETECTED entries, optionally note it.
            if result and self._suppressed_not_detected:
                # Emit a compact summary line before the DETECTED log.
                self.main_logger.debug(f"[detection] Suppressed {self._suppressed_not_detected} repeated NOT_DETECTED events")
                self._suppressed_not_detected = 0

            self._last_detection_success = result
        # Use log_action outside the lock (it acquires lock again) to keep consistency
        self.log_action("DETECTION", action_details, success=result)
    
    def log_click(self, position: tuple, click_type: str = "single", success: bool = True):
        """Log mouse click events"""
        self.log_action("MOUSE_CLICK", {
            "position": position,
            "click_type": click_type
        }, success=success)
    
    def log_monitoring(self, action: str, rule_count: int = 0, success: bool = True):
        """Log monitoring events"""
        details = {"action": action}
        if rule_count > 0:
            details["rules"] = rule_count
        
        self.log_action("MONITORING", details, success=success)
    
    def log_rule_match(self, rule_logic: str, condition_count: int, position: tuple):
        """Log rule matching events"""
        self.log_action("RULE_MATCHED", {
            "logic": rule_logic,
            "conditions": condition_count,
            "position": position
        }, success=True)
    
    def log_delay_popup(self, action: str, delay_seconds: int = 0, popup_enabled: bool = False):
        """Log delay and popup events"""
        details = {"action": action}
        if delay_seconds > 0:
            details["delay"] = f"{delay_seconds}s"
        if popup_enabled:
            details["popup"] = "enabled"
        
        self.log_action("DELAY_POPUP", details, success=True)
    
    def get_recent_logs(self, log_type: str = "main", lines: int = 100) -> List[str]:
        """
        Get recent log entries.
        
        Args:
            log_type: Type of log ('main', 'error', 'action')
            lines: Number of recent lines to retrieve
            
        Returns:
            List of log lines
        """
        log_file_map = {
            "main": self.main_log_file,
            "error": self.error_log_file,
            "action": self.action_log_file
        }
        
        log_file = log_file_map.get(log_type, self.main_log_file)
        
        try:
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        
        except Exception as e:
            self.log_error(f"Failed to read log file {log_file}", "logger", e)
            return [f"Error reading log file: {str(e)}"]

    # --- Compatibility helpers used by monitoring UI ---
    def get_logs_by_type(self, log_type: str, lines: int = 500) -> List[str]:
        """Return recent logs for a given type ('main', 'error', 'action')."""
        return self.get_recent_logs(log_type, lines)

    def get_all_logs(self, lines: int = 500) -> List[str]:
        """Return combined recent logs from main log. Kept for UI compatibility."""
        return self.get_recent_logs("main", lines)

    def clear_all_logs(self):
        """Clear all log files (compatibility wrapper)."""
        self.clear_logs("all")
    
    def get_log_stats(self) -> dict:
        """Get statistics about log files"""
        stats = {}
        
        log_files = {
            "main": self.main_log_file,
            "error": self.error_log_file,
            "action": self.action_log_file
        }
        
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
        """
        Clear log files.
        
        Args:
            log_type: Type of log to clear ('main', 'error', 'action', 'all')
        """
        log_files = []
        
        if log_type == "all":
            log_files = [self.main_log_file, self.error_log_file, self.action_log_file]
        elif log_type == "main":
            log_files = [self.main_log_file]
        elif log_type == "error":
            log_files = [self.error_log_file]
        elif log_type == "action":
            log_files = [self.action_log_file]
        
        for log_file in log_files:
            try:
                if log_file.exists():
                    log_file.unlink()
                    self.log_info(f"Cleared log file: {log_file.name}", "logger")
            except Exception as e:
                self.log_error(f"Failed to clear log file {log_file.name}", "logger", e)
    
    def export_logs(self, export_path: str, log_type: str = "all") -> bool:
        """
        Export logs to a specified path.
        
        Args:
            export_path: Path to export logs to
            log_type: Type of logs to export
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if log_type == "all":
                log_files = [
                    (self.main_log_file, f"autoclicker_main_{timestamp}.log"),
                    (self.error_log_file, f"autoclicker_errors_{timestamp}.log"),
                    (self.action_log_file, f"autoclicker_actions_{timestamp}.log")
                ]
            else:
                log_file_map = {
                    "main": self.main_log_file,
                    "error": self.error_log_file,
                    "action": self.action_log_file
                }
                source_file = log_file_map.get(log_type)
                if source_file:
                    log_files = [(source_file, f"autoclicker_{log_type}_{timestamp}.log")]
                else:
                    return False
            
            for source_file, dest_name in log_files:
                if source_file.exists():
                    dest_path = export_dir / dest_name
                    dest_path.write_text(source_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            self.log_info(f"Exported logs to {export_path}", "logger")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to export logs to {export_path}", "logger", e)
            return False
    
    def close(self):
        """Close the logging system"""
        self.log_info("=== Autoclicker Session Ended ===")
        
        # Close all handlers
        for logger in [self.main_logger, self.error_logger, self.action_logger]:
            for handler in logger.handlers:
                handler.close()


# Global logger instance
_logger_instance: Optional[AutoclickerLogger] = None


def get_logger() -> AutoclickerLogger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AutoclickerLogger()
    return _logger_instance


def init_logger(log_dir: str = "logs") -> AutoclickerLogger:
    """Initialize the global logger"""
    global _logger_instance
    if _logger_instance is not None:
        _logger_instance.close()
    _logger_instance = AutoclickerLogger(log_dir)
    return _logger_instance


def close_logger():
    """Close the global logger"""
    global _logger_instance
    if _logger_instance is not None:
        _logger_instance.close()
        _logger_instance = None
