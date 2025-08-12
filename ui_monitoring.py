import tkinter as tk
from tkinter import ttk, messagebox
from config import Rule


class UIMonitoringMixin:
    """
    Mixin class for monitoring and logging functionality.
    Contains methods for starting/stopping monitoring and managing logs.
    """
    
    def setup_monitoring_tab(self):
        """Set up the monitoring and logs tab."""
        # Create monitoring tab frame with reduced padding
        self.monitoring_frame = ttk.Frame(self.notebook, padding=(6, 6))  # Reduced from (8, 8)
        self.notebook.add(self.monitoring_frame, text="Monitoring & Logs")
        
        # Configure grid weights
        self.monitoring_frame.grid_columnconfigure(0, weight=1)
        self.monitoring_frame.grid_rowconfigure(1, weight=1)  # Logs area should expand
        
        # Real-time monitoring section
        self.create_monitoring_section()
        
        # Activity logs section  
        self.create_logs_section()
        
    def create_monitoring_section(self):
        """Create the real-time monitoring section."""
        monitor_frame = ttk.LabelFrame(self.monitoring_frame, text="Real-time Monitor", padding=(6, 4))  # Reduced padding
        monitor_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))  # Reduced pady
        monitor_frame.columnconfigure(1, weight=1)
        
        # Status display
        ttk.Label(monitor_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.monitor_status_label = ttk.Label(monitor_frame, text="Not monitoring", foreground="orange")
        self.monitor_status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Click count
        ttk.Label(monitor_frame, text="Clicks performed:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.click_count_label = ttk.Label(monitor_frame, text="0")
        self.click_count_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Last action
        ttk.Label(monitor_frame, text="Last action:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.last_action_label = ttk.Label(monitor_frame, text="None")
        self.last_action_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # Monitor controls
        control_frame = ttk.Frame(monitor_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        self.start_monitor_button = ttk.Button(control_frame, text="Start Monitoring", 
                                             command=self.start_monitoring)
        self.start_monitor_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_monitor_button = ttk.Button(control_frame, text="Stop Monitoring", 
                                            command=self.stop_monitoring, state='disabled')
        self.stop_monitor_button.pack(side=tk.LEFT)
        
    def create_logs_section(self):
        """Create the activity logs section."""
        logs_frame = ttk.LabelFrame(self.monitoring_frame, text="Activity Logs", padding=(6, 4))  # Reduced padding
        logs_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(1, weight=1)
        
        # Log controls
        log_controls = ttk.Frame(logs_frame)
        log_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 4))  # Reduced pady
        
        ttk.Button(log_controls, text="Refresh Logs", 
                  command=self.refresh_all_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_controls, text="Clear All Logs", 
                  command=self.clear_all_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_controls, text="Export Logs", 
                  command=self.export_all_logs).pack(side=tk.LEFT)
        
        # Logs notebook for different log types
        self.logs_notebook = ttk.Notebook(logs_frame)
        self.logs_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create log tabs
        self.create_log_tabs()
        
    def create_log_tabs(self):
        """Create tabs for different log types."""
        # Log types and their display names
        log_types = {
            "Actions": "action",
            "Monitoring": "monitoring", 
            "Errors": "error",
            "All Logs": "main"
        }
        
        self.log_texts = {}
        
        for tab_name, log_type in log_types.items():
            # Create frame for this log type
            log_frame = ttk.Frame(self.logs_notebook)
            self.logs_notebook.add(log_frame, text=tab_name)
            
            # Create scrolled text widget
            text_frame = ttk.Frame(log_frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.log_texts[log_type] = text_widget
            
            # Add controls for this log type
            controls_frame = ttk.Frame(log_frame)
            controls_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            ttk.Button(controls_frame, text=f"Refresh {tab_name}", 
                      command=lambda lt=log_type: self.refresh_logs(self.log_texts[lt], lt)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(controls_frame, text=f"Clear {tab_name}", 
                      command=lambda lt=log_type: self.clear_log_type(lt)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(controls_frame, text=f"Export {tab_name}", 
                      command=lambda lt=log_type: self.export_log_type(lt)).pack(side=tk.LEFT)
        
        # Load initial logs
        self.refresh_all_logs()
        
    def start_monitoring(self):
        """Start the autoclicker monitoring"""
        # Combine all conditions and groups for validation
        total_conditions = len(self.conditions) + sum(len(g.conditions) for g in self.condition_groups)
        if total_conditions == 0:
            messagebox.showerror("No Conditions", "Please add at least one condition before starting monitoring.")
            return

        # --- macOS permission / environment quick preflight (only runs once per session) ---
        if not hasattr(self, '_monitor_preflight_done'):
            self._monitor_preflight_done = True
            try:
                import sys  # type: ignore
                import pyautogui  # type: ignore
                # Try a tiny size / screen query – these are the first things that fail without permissions
                sz = pyautogui.size()
                ok = True
                try:
                    img = pyautogui.screenshot(region=(0, 0, min(4, sz[0]), min(4, sz[1])))
                    if img is None:
                        ok = False
                except Exception as shot_err:
                    ok = False
                    shot_exc = shot_err
                if not ok and sys.platform == 'darwin':
                    # Provide user guidance BEFORE proceeding so they know why start will fail silently later
                    guidance = (
                        "Screen capture failed – likely missing permissions.\n\n"
                        "Grant BOTH: System Settings > Privacy & Security >\n"
                        "  • Screen Recording\n  • Accessibility\n\n"
                        "Then re-launch the app (after fully quitting). If you are running from the DMG, copy the app to /Applications first."
                    )
                    try:
                        self.logger.log_error(f"Preflight screen capture failed: {shot_exc}", "monitoring")  # type: ignore
                    except Exception:
                        pass
                    messagebox.showerror("Permissions Required", guidance)
                    return
            except Exception as e:  # Non-fatal; just log
                try:
                    self.logger.log_warning(f"Preflight permission check warning: {e}", "monitoring")
                except Exception:
                    pass

        # Early diagnostic log
        try:
            self.logger.log_action("START_MONITORING_ATTEMPT", {
                "standalone_conditions": len(self.conditions),
                "group_count": len(self.condition_groups),
                "total_conditions": total_conditions,
                "has_selected_click_position": bool(self.selected_click_position)
            }, success=True)
        except Exception:
            pass

        # Reset click counter for new monitoring session
        self.click_count = 0
        self.update_monitor_display()

        # Require explicit click position selection
        if not self.selected_click_position:
            # Provide more guidance in packaged builds where users may confuse a condition position vs click position.
            messagebox.showerror(
                "Click Position Required",
                "You must set the global Click Position (where the automated click occurs).\n\n"
                "Tip: Use the 'Set Click Position' control in the Settings/Configuration tab."
            )
            return
        click_pos = self.selected_click_position

        # Build the rule with both standalone and group conditions
        rule = Rule(
            click_position=click_pos,
            condition_groups=self.condition_groups.copy(),
            group_logic=self.logic.get() if hasattr(self, 'logic') and self.logic.get() else 'any',
            conditions=self.conditions.copy() if self.conditions else None,
            logic=None,
            n=None
        )

        self.config.rules = [rule]
        self.config.delay = int(self.delay.get()) if hasattr(self, 'delay') and self.delay.get().isdigit() else 0
        self.config.popup = self.popup_var.get() if hasattr(self, 'popup_var') else True

        # Create and start monitor
        from monitor import ScreenMonitor
        self.monitor = ScreenMonitor(self.config)
        self.monitor.set_rule_matched_callback(self.on_rule_matched)

        started = False
        try:
            started = self.monitor.start_monitoring()
        except Exception as e:
            # Log unexpected start failure
            try:
                self.logger.log_error(f"Exception starting monitor: {e}", "monitoring")
            except Exception:
                pass
            messagebox.showerror("Monitor Error", f"Exception starting monitor: {e}")
            return

        if started:
            self.start_monitor_button.config(state='disabled')
            self.start_button.config(state='disabled') if hasattr(self, 'start_button') else None
            self.stop_monitor_button.config(state='normal')
            self.stop_button.config(state='normal') if hasattr(self, 'stop_button') else None
            # Lock configuration tab while monitoring
            if hasattr(self, 'lock_configuration'):
                self.lock_configuration(True)
            
            if hasattr(self, 'monitor_status_label') and self.monitor_status_label:
                self.monitor_status_label.config(text="✅ Monitoring active", foreground="green")
            self.status_label.config(text="Monitoring active...") if hasattr(self, 'status_label') else None
            if hasattr(self, 'last_action_label') and self.last_action_label:
                self.last_action_label.config(text="Monitoring started")
            
            # Log monitoring start
            self.logger.log_monitoring("START", success=True)
            self.logger.log_action("START_MONITORING", {
                "total_conditions": total_conditions,
                "click_position": click_pos
            }, success=True)
        else:
            # Provide detailed diagnostics when start fails silently
            diag = {
                "is_monitoring_flag": getattr(self, 'monitor', None).is_monitoring if getattr(self, 'monitor', None) else None,
                "rules_in_config": len(self.config.rules) if hasattr(self.config, 'rules') else 'n/a',
                "rule_click_pos": getattr(self.config.rules[0], 'click_position', None) if getattr(self, 'config', None) and self.config.rules else None
            }
            try:
                self.logger.log_action("START_MONITORING_FAILED", diag, success=False)
            except Exception:
                pass
            messagebox.showerror(
                "Monitor Error",
                "Failed to start monitoring.\n\nDiagnostics:" \
                f"\n  is_monitoring={diag['is_monitoring_flag']}" \
                f"\n  rules={diag['rules_in_config']}" \
                f"\n  click_pos={diag['rule_click_pos']}" \
                "\n\nConfirm you granted Screen Recording & Accessibility permissions on macOS."
            )
        
    def stop_monitoring(self):
        """Stop the autoclicker monitoring"""
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.stop_monitoring()
            self.monitor = None
            
        # Cancel any active delay/popup
        if hasattr(self, 'delay_popup_manager') and self.delay_popup_manager:
            self.delay_popup_manager.cancel_current_action()
            
        # Update UI states
        self.start_monitor_button.config(state='normal')
        self.start_button.config(state='normal') if hasattr(self, 'start_button') else None
        self.stop_monitor_button.config(state='disabled')
        self.stop_button.config(state='disabled') if hasattr(self, 'stop_button') else None
        # Unlock configuration tab after stopping
        if hasattr(self, 'lock_configuration'):
            self.lock_configuration(False)
        
        if hasattr(self, 'monitor_status_label') and self.monitor_status_label:
            self.monitor_status_label.config(text="⏹️ Monitoring stopped", foreground="orange")
        self.status_label.config(text="Monitoring stopped") if hasattr(self, 'status_label') else None
        if hasattr(self, 'last_action_label') and self.last_action_label:
            self.last_action_label.config(text="Monitoring stopped")
        
        # Log monitoring stop
        self.logger.log_monitoring("STOP", success=True)
        self.logger.log_action("STOP_MONITORING", {}, success=True)
        
    def on_rule_matched(self, rule):
        """Callback when a rule is matched"""
        # Log rule match - handle both new and old rule structures
        if hasattr(rule, 'condition_groups') and rule.condition_groups:
            logic = rule.group_logic or 'any'
            total_conditions = sum(len(g.conditions) for g in rule.condition_groups)
            position = rule.click_position
        elif hasattr(rule, 'conditions') and rule.conditions:
            logic = rule.logic or 'any'
            total_conditions = len(rule.conditions)
            position = rule.click_position
        else:
            logic = 'any'
            total_conditions = 0
            position = (0, 0)
            
        self.logger.log_rule_match(logic, total_conditions, position)
        
        # Update monitor display
        if hasattr(self, 'last_action_label') and self.last_action_label:
            self.last_action_label.config(text="Rule matched - processing...")
        
        # Get current config settings
        delay_seconds = self.config.delay if hasattr(self.config, 'delay') else 0
        show_popup = self.config.popup if hasattr(self.config, 'popup') else True
        
        # Override popup setting: don't show popup if delay is 0
        if delay_seconds == 0:
            show_popup = False
        else:
            show_popup = show_popup
        
        # Create rule info string for display
        if hasattr(rule, 'condition_groups') and rule.condition_groups:
            group_count = len(rule.condition_groups)
            condition_count = sum(len(g.conditions) for g in rule.condition_groups)
            rule_info = f"{group_count} group(s) with {condition_count} condition(s)"
        elif hasattr(rule, 'conditions') and rule.conditions:
            rule_info = f"{len(rule.conditions)} condition(s)"
        else:
            rule_info = "No conditions"
        
        # Log delay/popup start
        self.logger.log_delay_popup("START", delay_seconds=delay_seconds, popup_enabled=show_popup)
        
        # Handle delay and popup using DelayPopupManager
        self.delay_popup_manager.handle_rule_matched(
            delay_seconds=delay_seconds,
            show_popup=show_popup,
            proceed_callback=lambda: self.execute_click_action(rule),
            rule_info=rule_info,
            cancelled_callback=self.on_action_cancelled,
            stop_monitoring_callback=self.stop_monitoring
        )
        
    def execute_click_action(self, rule):
        """Execute the click action after delay/popup confirmation"""
        self.last_action_label.config(text="Executing click...")
        self.status_label.config(text="Executing click action...") if hasattr(self, 'status_label') else None
        
        try:
            # Get click type from UI
            click_type = self.click_type.get() if hasattr(self, 'click_type') else 'single'
            
            # Perform the click
            success = self.mouse_clicker.click_at_position(rule.click_position, click_type)
            
            if success:
                self.click_count += 1
                self.update_monitor_display()
                if hasattr(self, 'last_action_label') and self.last_action_label:
                    self.last_action_label.config(text=f"✅ Click #{self.click_count} successful")
                
                self.logger.log_action("EXECUTE_CLICK", {
                    "position": rule.click_position,
                    "click_type": click_type,
                    "click_number": self.click_count
                }, success=True)
            else:
                if hasattr(self, 'last_action_label') and self.last_action_label:
                    self.last_action_label.config(text="❌ Click failed")
                self.logger.log_error("Click execution failed", "clicker")
                
        except Exception as e:
            if hasattr(self, 'last_action_label') and self.last_action_label:
                self.last_action_label.config(text="❌ Click error")
            self.logger.log_error(f"Click execution error: {e}", "clicker")
        
        # Reset status after a delay
        if hasattr(self, 'root'):
            self.root.after(2000, lambda: self.update_monitor_display())
        
        # Resume monitoring after click action is complete
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.resume_monitoring()
    
    def on_action_cancelled(self):
        """Callback when user cancels the action"""
        if hasattr(self, 'last_action_label') and self.last_action_label:
            self.last_action_label.config(text="❌ Action cancelled by user")
        self.status_label.config(text="❌ Action cancelled by user") if hasattr(self, 'status_label') else None
        
        # Log the cancellation
        self.logger.log_action("CANCEL_ACTION", {}, success=True)
        
        print("❌ User cancelled the click action")
        
        # Resume monitoring after cancellation
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.resume_monitoring()
        
        # Reset status after a delay
        if hasattr(self, 'root'):
            self.root.after(2000, lambda: self.update_monitor_display())
            
    def update_monitor_display(self):
        """Update the monitoring display with current status."""
        if not hasattr(self, 'click_count_label') or not hasattr(self, 'monitor_status_label') or self.monitor_status_label is None:
            return
            
        if self.monitor and self.monitor.is_monitoring:
            self.monitor_status_label.config(text="✅ Monitoring active", foreground="green")
        else:
            self.monitor_status_label.config(text="⏹️ Not monitoring", foreground="orange")
        
    def show_logs_window(self):
        """Show the logs viewing window (legacy method, now switches to monitoring tab)"""
        self.logger.log_action("OPEN_LOGS", {}, success=True)
        
        # Switch to monitoring tab
        if hasattr(self, 'notebook'):
            # Find the monitoring tab
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Monitoring & Logs":
                    self.notebook.select(i)
                    break
        
    def refresh_logs(self, text_widget: tk.Text, log_type: str):
        """Refresh logs in the text widget"""
        try:
            # Clear the text widget
            text_widget.delete(1.0, tk.END)
            
            # Get logs from logger
            if log_type == "main":
                logs = self.logger.get_all_logs()
            else:
                logs = self.logger.get_logs_by_type(log_type)
            
            # Insert logs into text widget
            for log_entry in logs[-100:]:  # Show last 100 entries
                text_widget.insert(tk.END, log_entry + "\n")
                
            # Scroll to bottom
            text_widget.see(tk.END)
            
        except Exception as e:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, f"Error loading logs: {e}")
    
    def refresh_all_logs(self):
        """Refresh all log tabs"""
        if hasattr(self, 'log_texts'):
            for log_type, text_widget in self.log_texts.items():
                self.refresh_logs(text_widget, log_type)
    
    def clear_log_type(self, log_type: str):
        """Clear logs of specified type"""
        result = messagebox.askyesno("Confirm Clear", 
                                   f"Are you sure you want to clear all {log_type} logs?\n"
                                   "This action cannot be undone.")
        if result:
            try:
                self.logger.clear_logs(log_type)
                # Refresh the corresponding text widget
                if log_type in self.log_texts:
                    self.refresh_logs(self.log_texts[log_type], log_type)
                messagebox.showinfo("Clear Successful", f"{log_type.title()} logs cleared.")
            except Exception as e:
                messagebox.showerror("Clear Error", f"Failed to clear logs: {e}")
    
    def clear_all_logs(self):
        """Clear all logs"""
        result = messagebox.askyesno("Confirm Clear All", 
                                   "Are you sure you want to clear ALL logs?\n"
                                   "This action cannot be undone.")
        if result:
            try:
                self.logger.clear_all_logs()
                self.refresh_all_logs()
                messagebox.showinfo("Clear Successful", "All logs cleared.")
            except Exception as e:
                messagebox.showerror("Clear Error", f"Failed to clear logs: {e}")
    
    def export_log_type(self, log_type: str):
        """Export logs of specified type"""
        from tkinter import filedialog
        export_dir = filedialog.askdirectory(title=f"Select directory to export {log_type} logs")
        if export_dir:
            try:
                filename = self.logger.export_logs(log_type, export_dir)
                messagebox.showinfo("Export Successful", f"Logs exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export logs: {e}")
    
    def export_all_logs(self):
        """Export all logs"""
        from tkinter import filedialog
        export_dir = filedialog.askdirectory(title="Select directory to export all logs")
        if export_dir:
            try:
                exported_files = []
                for log_type in ["action", "monitoring", "error", "main"]:
                    filename = self.logger.export_logs(log_type, export_dir)
                    exported_files.append(filename)
                    
                messagebox.showinfo("Export Successful", 
                                  "All logs exported to:\n" + "\n".join(exported_files))
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export logs: {e}")
