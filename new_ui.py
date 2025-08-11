import tkinter as tk
from tkinter import messagebox
import datetime

from config import Config
from delay_popup import DelayPopupManager
from clicker import MouseClicker
from logger import get_logger

# Import our modular UI components
from ui_components import UIComponentsMixin
from ui_conditions import UIConditionsMixin
from ui_groups import UIGroupsMixin
from ui_config import UIConfigMixin
from ui_monitoring import UIMonitoringMixin

# Optional: modern theming with ttkbootstrap (falls back gracefully if unavailable)
try:
    import ttkbootstrap as ttkb
except Exception:  # pragma: no cover - optional dependency
    ttkb = None


class ModernAutoclickerUI(UIComponentsMixin, UIConditionsMixin, UIGroupsMixin, 
                         UIConfigMixin, UIMonitoringMixin):
    """
    Modern Autoclicker UI with modular design.
    Inherits functionality from multiple mixins to keep the codebase organized.
    
    This modern implementation maintains 1:1 functionality with the original ui.py
    but with better organization, modern styling, and a tabbed interface.
    
    Key Features:
    - Tabbed interface with Configuration and Monitoring & Logs tabs
    - Real-time monitoring display
    - Integrated activity logs with multiple views
    - Modern styling with ttkbootstrap support
    - Modular codebase split across multiple files for maintainability
    """
    
    def __init__(self):
        # Create root window first
        self.root = tk.Tk()

        # Apply a modern theme if ttkbootstrap is available
        self.style = None
        if ttkb is not None:
            try:
                self.style = ttkb.Style("flatly")  # Modern light theme
                self.root = self.style.master
            except Exception:
                self.style = None

        self.root.title("AutoClicker Pro - Advanced Automation Suite")
        
        # Configure grid weights first
        try:
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(0, weight=1)
        except Exception:
            pass
        
        # Set reasonable minimum size and let content determine initial size
        self.root.minsize(800, 600)
        
        # Don't set initial geometry - let the window size to content
        # Will be set after UI is created based on content

        # Initialize logger
        self.logger = get_logger()
        self.logger.log_info("Modern Autoclicker UI initialized", "ui")

        # Initialize core components
        self.config = Config(rules=[])
        self.monitor = None
        self.delay_popup_manager = DelayPopupManager()
        self.delay_popup_manager.set_parent_window(self.root)
        self.mouse_clicker = MouseClicker()

        # Always initialize these attributes
        self.selected_click_position = None
        self.selected_position = None
        self.selected_area = None
        self.selected_color = None
        self.conditions = []
        self.condition_groups = []
        self.click_count = 0

        # Initialize UI variables before setup_ui
        self.config_name_var = tk.StringVar()  # Optional config name

        # Initialize monitoring widgets that other mixins might need (before setup_ui)
        self.monitor_status_label = None
        self.click_count_label = None
        self.last_action_label = None

        # Set up the modern UI
        self.setup_ui()
        
        # Size window to content and center it
        self.size_window_to_content()
        
        # Optimize window size after UI creation
        self.root.after(100, self.optimize_window_size)
        
        # Set up window resizing constraints
        self.setup_window_constraints()
        
        # Initialize the selected color to None
        self.selected_color = None
        
    def size_window_to_content(self):
        """Size the window to fit its content properly and center it."""
        # Update all widgets to get accurate size
        self.root.update_idletasks()
        
        # Get the required size for the content with proper calculations
        # Consider both tabs and pick the larger requirement
        notebook_width = self.notebook.winfo_reqwidth()
        notebook_height = self.notebook.winfo_reqheight()
        
        # Add minimal padding for window chrome
        padding_x = 20
        padding_y = 60  # Reduced from 100 for title bar and tabs
        
        width = notebook_width + padding_x
        height = notebook_height + padding_y
        
        # Set reasonable bounds
        min_width, min_height = 800, 600
        max_width, max_height = 1200, 800  # Reduced max height from 900 to 800
        
        width = max(min(width, max_width), min_width)
        height = max(min(height, max_height), min_height)
        
        # Center the window on screen
        self.center_window(self.root, width, height)
        
    def center_window(self, window, width, height):
        """Center a window on the screen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_window_constraints(self):
        """Set up proper window resizing constraints."""
        # Make window resizable
        self.root.resizable(True, True)
        
        # Bind to window configuration changes
        self.root.bind('<Configure>', self.on_window_configure)
        
    def on_window_configure(self, event):
        """Handle window resize events to maintain proper scaling."""
        # Only handle window (root) resize events, not child widgets
        if event.widget == self.root:
            # Update scroll region when window is resized
            if hasattr(self, 'canvas'):
                self.root.after_idle(lambda: self.canvas.configure(
                    scrollregion=self.canvas.bbox("all")
                ))
                
            # If window was resized smaller than content, ensure content is still accessible
            if hasattr(self, 'scrollable_frame'):
                self.root.after_idle(self._ensure_content_visibility)
                
    def _ensure_content_visibility(self):
        """Ensure all content remains visible and accessible."""
        if hasattr(self, 'canvas') and hasattr(self, 'scrollable_frame'):
            # Update canvas scroll region
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)
        
    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()
        
    def new_config(self):
        """Create a new blank configuration and reset the UI."""
        if hasattr(self, 'monitor') and self.monitor and getattr(self.monitor, 'is_monitoring', False):
            self.stop_monitoring()

        # Clear all conditions and groups
        self.conditions = []
        self.condition_groups = []
        self.selected_click_position = None
        self.selected_position = None
        self.selected_area = None
        self.selected_color = None

        # Clear the configuration name
        if hasattr(self, 'config_name_var'):
            self.config_name_var.set("")

        # Reset the UI through the components mixin
        self.reset_ui_state()

        # Create a new config
        self.config = Config(rules=[])

        if hasattr(self, 'logger'):
            self.logger.log_info("Created new configuration", "ui")
        messagebox.showinfo("New Configuration", "Created a new blank configuration.")

    def get_current_timestamp(self):
        """Get current timestamp for default filenames."""
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d_%H%M")


if __name__ == "__main__":
    app = ModernAutoclickerUI()
    app.run()
