"""
Delay and popup management for autoclicker - handles user intervention before clicking.
"""

import time
import threading
import tkinter as tk
from typing import Callable, Optional


class DelayPopupManager:
    """Manages delay and popup functionality before executing clicks"""
    
    def __init__(self):
        self.delay_thread: Optional[threading.Thread] = None
        self.popup_window: Optional[tk.Toplevel] = None
        self.is_cancelled = False
        self.on_proceed_callback: Optional[Callable] = None
        self.on_cancelled_callback: Optional[Callable] = None  # New callback for cancellation
        self.on_stop_monitoring_callback: Optional[Callable] = None  # Callback to stop monitoring
        self.parent_window: Optional[tk.Tk] = None
        
    def set_parent_window(self, parent: tk.Tk) -> None:
        """Set the parent window for popup positioning"""
        self.parent_window = parent
        
    def handle_rule_matched(self, delay_seconds: int, show_popup: bool, 
                          proceed_callback: Callable, rule_info: str = "", 
                          cancelled_callback: Optional[Callable] = None,
                          stop_monitoring_callback: Optional[Callable] = None) -> None:
        """
        Handle a rule match with optional delay and popup.
        
        Args:
            delay_seconds: Delay in seconds before proceeding
            show_popup: Whether to show confirmation popup
            proceed_callback: Function to call if user doesn't cancel
            rule_info: Information about the matched rule for display
            cancelled_callback: Function to call if user cancels
            stop_monitoring_callback: Function to call to stop monitoring entirely
        """
        self.is_cancelled = False
        self.on_proceed_callback = proceed_callback
        self.on_cancelled_callback = cancelled_callback
        self.on_stop_monitoring_callback = stop_monitoring_callback
        
        if delay_seconds > 0 or show_popup:
            # Start delay/popup handling in separate thread
            self.delay_thread = threading.Thread(
                target=self._handle_delay_popup,
                args=(delay_seconds, show_popup, rule_info),
                daemon=True
            )
            self.delay_thread.start()
        else:
            # No delay or popup, proceed immediately
            if self.on_proceed_callback:
                self.on_proceed_callback()
                
    def cancel_current_action(self) -> None:
        """Cancel the current delay/popup action"""
        self.is_cancelled = True
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
            
    def _handle_delay_popup(self, delay_seconds: int, show_popup: bool, rule_info: str) -> None:
        """Handle delay and popup - NEW LOGIC: popup IS the delay mechanism"""
        try:
            if show_popup and delay_seconds > 0:
                # Show popup immediately and start countdown within popup
                self._show_confirmation_popup(rule_info, delay_seconds)
                # Start countdown thread that will auto-execute after delay
                self._start_countdown_thread(delay_seconds)
            elif show_popup and delay_seconds == 0:
                # Show popup without delay for immediate confirmation
                self._show_confirmation_popup(rule_info, delay_seconds)
            else:
                # No popup - handle delay then proceed directly
                if delay_seconds > 0:
                    print(f"No popup - delaying for {delay_seconds} seconds...")
                    for i in range(delay_seconds):
                        if self.is_cancelled:
                            return
                        time.sleep(1)
                        print(f"Delay: {delay_seconds - i - 1} seconds remaining...")
                
                # Check if cancelled during delay
                if not self.is_cancelled and self.on_proceed_callback:
                    self.on_proceed_callback()
                    
        except Exception as e:
            print(f"Error in delay/popup handling: {e}")
    
    def _start_countdown_thread(self, delay_seconds: int) -> None:
        """Start countdown in popup that auto-executes after delay"""
        countdown_thread = threading.Thread(
            target=self._run_popup_countdown,
            args=(delay_seconds,),
            daemon=True
        )
        countdown_thread.start()
    
    def _run_popup_countdown(self, delay_seconds: int) -> None:
        """Run countdown in popup and auto-execute when finished"""
        try:
            for i in range(delay_seconds):
                if self.is_cancelled:
                    return
                
                remaining = delay_seconds - i
                countdown_text = f"⏰ Auto-click in {remaining} seconds..."
                
                # Update countdown label in popup
                if self.popup_window and hasattr(self, 'countdown_label'):
                    self.popup_window.after(0, lambda text=countdown_text: self.countdown_label.config(text=text))
                
                print(f"⏰ Auto-click in {remaining} seconds...")
                time.sleep(1)
            
            # Time's up - auto execute if not cancelled
            if not self.is_cancelled:
                if self.popup_window and hasattr(self, 'countdown_label'):
                    self.popup_window.after(0, lambda: self.countdown_label.config(text="🚀 Executing NOW!"))
                print("🚀 Auto-executing click!")
                time.sleep(0.5)  # Brief pause to show final message
                
                # Close popup and execute
                self._auto_execute()
                
        except Exception as e:
            print(f"Error in popup countdown: {e}")
    
    def _auto_execute(self) -> None:
        """Auto-execute the action when countdown finishes"""
        # Close popup
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
        
        # Restore the main window
        if self.parent_window:
            self.parent_window.deiconify()
            self.parent_window.lift()
        
        # Execute callback
        if self.on_proceed_callback and not self.is_cancelled:
            if self.parent_window:
                self.parent_window.after(100, self.on_proceed_callback)
            else:
                self.on_proceed_callback()
            
    def _show_confirmation_popup(self, rule_info: str, delay_seconds: int = 0) -> None:
        """Show confirmation popup in main thread"""
        if self.parent_window is None:
            print("No parent window set for popup")
            return
            
        # Schedule popup creation in main thread
        self.parent_window.after(0, self._create_popup, rule_info, delay_seconds)
        
    def _create_popup(self, rule_info: str, delay_seconds: int = 0) -> None:
        """Create and show the confirmation popup"""
        if self.is_cancelled:
            return
            
        # Store delay for later use
        self._current_delay_seconds = delay_seconds
        
        # Hide the main window
        if self.parent_window:
            self.parent_window.withdraw()
            
        self.popup_window = tk.Toplevel(self.parent_window)
        self.popup_window.title("Autoclicker Confirmation")
        # Increased height significantly to ensure buttons are always visible
        window_height = 400 if delay_seconds > 0 else 350
        window_width = 550
        self.popup_window.geometry(f"{window_width}x{window_height}")  # Made wider and taller
        self.popup_window.resizable(False, False)
        
        # Center the popup on screen
        self.popup_window.update_idletasks()  # Update to get actual window size
        screen_width = self.popup_window.winfo_screenwidth()
        screen_height = self.popup_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.popup_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make popup modal and on top
        self.popup_window.transient(self.parent_window)
        self.popup_window.grab_set()
        self.popup_window.attributes('-topmost', True)
        
        # Create popup content
        main_frame = tk.Frame(self.popup_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon and message
        icon_label = tk.Label(main_frame, text="⚠️", font=("Arial", 24))
        icon_label.pack(pady=10)
        
        message_text = "Rule conditions have been met!\nCountdown is running..."
        if delay_seconds > 0:
            message_text += f"\n\n⏱️ Auto-click in {delay_seconds} seconds\n• Click 'PROCEED' to skip countdown\n• Click 'CANCEL' to stop monitoring"
        else:
            message_text += "\n\n• Click 'PROCEED' to execute immediately\n• Click 'CANCEL' to stop monitoring"
        
        message_label = tk.Label(
            main_frame, 
            text=message_text,
            font=("Arial", 11),
            justify=tk.CENTER,
            wraplength=400  # Allow text wrapping within window width
        )
        message_label.pack(pady=(5, 15))
        
        # Add countdown label (initially hidden)
        self.countdown_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 18, "bold"),
            fg="red"
        )
        self.countdown_label.pack(pady=10)
        
        if rule_info:
            info_label = tk.Label(
                main_frame,
                text=f"Rule: {rule_info}",
                font=("Arial", 10),
                fg="gray"
            )
            info_label.pack(pady=5)
            
        # Create buttons with absolute positioning to ensure visibility
        proceed_button = tk.Button(
            main_frame, 
            text="PROCEED", 
            command=self._on_proceed_clicked,
            font=("Arial", 12, "bold"),
            bg="green",
            fg="white",
            width=12,
            height=2
        )
        proceed_button.place(x=100, y=320)  # Absolute position
        
        cancel_button = tk.Button(
            main_frame, 
            text="CANCEL", 
            command=self._on_cancel_clicked,
            font=("Arial", 12, "bold"),
            bg="red",
            fg="white",
            width=12,
            height=2
        )
        cancel_button.place(x=300, y=320)  # Absolute position
        
        # Auto-focus and key bindings
        proceed_button.focus_set()
        self.popup_window.bind('<Return>', lambda e: self._on_proceed_clicked())
        self.popup_window.bind('<Escape>', lambda e: self._on_cancel_clicked())
        
        # Handle window close
        self.popup_window.protocol("WM_DELETE_WINDOW", self._on_cancel_clicked)
        
        # Only auto-close if no delay is set (otherwise user should make conscious choice)
        if delay_seconds == 0:
            timeout_ms = 10000  # 10 seconds for no-delay situations
            self.popup_window.after(timeout_ms, self._auto_close_popup)
        # If there's a delay, let the user decide (no auto-close)
        
    def _on_proceed_clicked(self) -> None:
        """Handle proceed button click - skip countdown and execute immediately"""
        print("✅ User clicked Proceed - skipping countdown!")
        self.is_cancelled = True  # Stop the countdown thread
        
        # Close popup and restore main window
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
            
        # Restore the main window
        if self.parent_window:
            self.parent_window.deiconify()
            self.parent_window.lift()
            
        # Execute immediately
        if self.on_proceed_callback:
            if self.parent_window:
                self.parent_window.after(100, self.on_proceed_callback)
            else:
                self.on_proceed_callback()
    
    def _handle_delay_then_click(self, delay_seconds: int) -> None:
        """Handle delay countdown after user confirmation, then execute click"""
        try:
            print(f"✅ User confirmed - starting {delay_seconds} second countdown...")
            
            # Show countdown in popup
            for i in range(delay_seconds):
                if self.is_cancelled:
                    return
                
                remaining = delay_seconds - i
                countdown_text = f"⏰ Clicking in {remaining} seconds..."
                
                # Update countdown label in popup
                if self.popup_window and hasattr(self, 'countdown_label'):
                    self.popup_window.after(0, lambda text=countdown_text: self.countdown_label.config(text=text))
                
                print(f"⏰ Click in {remaining} seconds...")
                time.sleep(1)
            
            # Final countdown message
            if not self.is_cancelled:
                if self.popup_window and hasattr(self, 'countdown_label'):
                    self.popup_window.after(0, lambda: self.countdown_label.config(text="🚀 Clicking NOW!"))
                print("🚀 Executing click now!")
                time.sleep(0.5)  # Brief pause to show final message
                
                # Close popup and restore main window
                if self.popup_window:
                    self.popup_window.destroy()
                    self.popup_window = None
                    
                if self.parent_window:
                    self.parent_window.deiconify()
                    self.parent_window.lift()
                    
            # Execute the callback after delay
            if not self.is_cancelled and self.on_proceed_callback:
                if self.parent_window:
                    self.parent_window.after(0, self.on_proceed_callback)
                else:
                    self.on_proceed_callback()
                    
        except Exception as e:
            print(f"Error in delay countdown: {e}")
    
    def _update_status_for_delay(self, delay_seconds: int):
        """Update status label to show delay countdown is starting"""
        # Try to find and update status label (this is a bit hacky but works)
        try:
            for widget in self.parent_window.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'config') and hasattr(child, 'cget'):
                            try:
                                if 'status' in str(child).lower():
                                    child.config(text=f"⏰ User confirmed! Countdown: {delay_seconds}s")
                                    break
                            except Exception:
                                pass
        except Exception:
            pass
    
    def _update_countdown_status(self, remaining: int):
        """Update status label with countdown"""
        try:
            for widget in self.parent_window.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'config') and hasattr(child, 'cget'):
                            try:
                                if 'status' in str(child).lower():
                                    child.config(text=f"⏰ Clicking in {remaining} seconds...")
                                    break
                            except Exception:
                                pass
        except Exception:
            pass
            
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click - stop monitoring entirely"""
        print("❌ User clicked Cancel - stopping monitoring!")
        self.is_cancelled = True
        
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
        
        # Restore the main window
        if self.parent_window:
            self.parent_window.deiconify()
            self.parent_window.lift()
        
        # Call stop monitoring callback to stop the entire monitoring process
        if self.on_stop_monitoring_callback:
            self.on_stop_monitoring_callback()
        
        # Also call cancellation callback if set
        if self.on_cancelled_callback:
            self.on_cancelled_callback()
        
    def _auto_close_popup(self) -> None:
        """Auto-close popup after timeout"""
        if self.popup_window and not self.is_cancelled:
            print("Popup timed out, proceeding automatically...")
            self._on_proceed_clicked()
            
    def is_active(self) -> bool:
        """Check if delay/popup is currently active"""
        return (self.delay_thread and self.delay_thread.is_alive()) or self.popup_window is not None
        
    def cleanup(self) -> None:
        """Clean up resources"""
        self.cancel_current_action()
        if self.delay_thread and self.delay_thread.is_alive():
            self.delay_thread.join(timeout=1.0)
