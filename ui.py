import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import json
 
from config import Condition, Rule, Config, ConditionGroup
from monitor import ScreenMonitor
from delay_popup import DelayPopupManager
from clicker import MouseClicker
from logger import get_logger

# Optional: modern theming with ttkbootstrap (falls back gracefully if unavailable)
try:
    import ttkbootstrap as ttkb
except Exception:  # pragma: no cover - optional dependency
    ttkb = None

class AutoclickerUI:
    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()
    def new_config(self):
        """Create a new blank configuration and reset the UI."""
        if hasattr(self, 'monitor') and self.monitor and getattr(self.monitor, 'is_monitoring', False):
            self.toggle_monitoring()

        # Clear all conditions and groups
        self.conditions = []
        self.condition_groups = []
        self.selected_click_position = None
        self.selected_position = None
        self.selected_area = None

        # Clear the configuration name
        if hasattr(self, 'config_name_var'):
            self.config_name_var.set("")

        # Reset the UI
        if hasattr(self, 'conditions_listbox'):
            self.conditions_listbox.delete(0, tk.END)
        if hasattr(self, 'groups_listbox'):
            for item in self.groups_listbox.get_children():
                self.groups_listbox.delete(item)

        # Reset labels
        if hasattr(self, 'pos_label'):
            self.pos_label.config(text="No position/area selected")
        if hasattr(self, 'click_pos_label'):
            self.click_pos_label.config(text="Click: Same as detection area")

        # Create a new config
        self.config = Config(rules=[])

        if hasattr(self, 'logger'):
            self.logger.log_info("Created new configuration", "ui")
        messagebox.showinfo("New Configuration", "Created a new blank configuration.")
    def __init__(self):
        # Create root window first
        self.root = tk.Tk()

        # Apply a modern theme if ttkbootstrap is available
        self.style = None
        if ttkb is not None:
            try:
                # Prefer a clean, modern light theme by default
                self.style = ttkb.Style(theme="cosmo")
                # Slightly larger default font for readability
                try:
                    self.style.configure('.', font=("SF Pro Text", 11))
                except Exception:
                    self.style.configure('.', font=("Helvetica", 11))
            except Exception:
                self.style = None

        self.root.title("Autoclicker")
        # Give a bit more room; make window responsive
        self.root.geometry("900x720")
        self.root.minsize(800, 600)
        try:
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(1, weight=1)
        except Exception:
            pass

        # Initialize logger
        self.logger = get_logger()
        self.logger.log_info("Autoclicker UI initialized", "ui")

        self.config = Config(rules=[])
        self.monitor = None
        self.delay_popup_manager = DelayPopupManager()
        self.delay_popup_manager.set_parent_window(self.root)
        self.mouse_clicker = MouseClicker()

        # Always initialize these attributes
        self.selected_click_position = None
        self.selected_position = None
        self.selected_area = None
        self.conditions = []
        self.condition_groups = []

        # Initialize UI variables before setup_ui
        self.config_name_var = tk.StringVar()  # Optional config name

        self.setup_ui()

        # Perform early permission checks (macOS screen recording & accessibility)
        self.check_and_request_permissions()
        
    def check_and_request_permissions(self):
        """Attempt to trigger macOS permission prompts early and warn user if missing.
        (Non-blocking best-effort – true granting must be done by user in System Settings.)"""
        import sys
        if sys.platform != 'darwin':
            return
        try:
            # Attempt a tiny screenshot to trigger Screen Recording permission prompt (if not already granted)
            img = pyautogui.screenshot()
            # Basic heuristic: if screenshot is uniformly black it could indicate missing permission
            # (Not definitive, but useful hint.)
            extrema = img.getextrema()
            all_black = False
            try:
                # extrema can be list for multiband
                all_black = all(ch[0] == 0 and ch[1] == 0 for ch in extrema)
            except Exception:
                pass
            # Attempt a benign position read to trigger Accessibility (control) permission
            _ = pyautogui.position()
            if all_black:
                messagebox.showwarning(
                    "Screen Recording Permission",
                    "The captured screen appears blank. If this is the first run, please grant 'Screen Recording' permission to this app (Python) in System Settings > Privacy & Security > Screen Recording, then restart the app."
                )
        except Exception as e:
            messagebox.showwarning(
                "Permissions Required",
                f"Unable to capture the screen or read mouse position.\nPlease grant BOTH 'Screen Recording' and 'Accessibility' permissions to Python in System Settings > Privacy & Security.\nError: {e}"
            )
        
    def setup_ui(self):
        # Create a menu bar
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Create File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Configuration", command=self.new_config)
        file_menu.add_command(label="Open Configuration...", command=self.load_config)
        file_menu.add_command(label="Save Configuration...", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Theme menu (only when ttkbootstrap is available)
        if self.style is not None:
            theme_menu = tk.Menu(menu_bar, tearoff=0)
            menu_bar.add_cascade(label="Theme", menu=theme_menu)
            themes = [
                ("Cosmo (Light)", "cosmo"),
                ("Flatly (Light)", "flatly"),
                ("Journal (Light)", "journal"),
                ("Morph (Light)", "morph"),
                ("Solar (Light)", "solar"),
                ("Cyborg (Dark)", "cyborg"),
                ("Darkly (Dark)", "darkly"),
                ("Superhero (Dark)", "superhero"),
            ]

            def _apply_theme(theme_name: str):
                try:
                    self.style.theme_use(theme_name)
                except Exception:
                    pass

            for label, name in themes:
                theme_menu.add_command(label=label, command=lambda n=name: _apply_theme(n))

        # Toolbar with most common actions
        toolbar = ttk.Frame(self.root, padding=(10, 6))
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(toolbar, text="New", command=self.new_config).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(toolbar, text="Open", command=self.load_config).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(toolbar, text="Save", command=self.save_config).grid(row=0, column=2, padx=6, pady=4)

        # Main frame
        main_frame = ttk.Frame(self.root, padding=(16, 12))
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        for c in range(2):
            main_frame.grid_columnconfigure(c, weight=1)
        for r in range(8):
            main_frame.grid_rowconfigure(r, weight=0)
        main_frame.grid_rowconfigure(5, weight=1)  # conditions frame grows

        # Config name field (optional)
        name_frame = ttk.LabelFrame(main_frame, text="Configuration Name (optional)", padding=(12, 10))
        name_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(name_frame, textvariable=self.config_name_var, width=30).grid(row=0, column=0, padx=8, pady=4, sticky=(tk.W, tk.E))
        name_frame.columnconfigure(0, weight=1)

        # Position selection (enhanced for areas)
        pos_frame = ttk.LabelFrame(main_frame, text="Detection Area", padding=(12, 10))
        pos_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(pos_frame, text="Select Point", command=self.select_position).grid(row=0, column=0, padx=6, pady=2)
        ttk.Button(pos_frame, text="Select Area", command=self.select_area).grid(row=0, column=1, padx=6, pady=2)

        self.pos_label = ttk.Label(pos_frame, text="No position/area selected")
        self.pos_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        # Click position (separate from detection)
        click_frame = ttk.LabelFrame(main_frame, text="Click Position", padding=(12, 10))
        click_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(click_frame, text="Set Click Position", command=self.select_click_position).grid(row=0, column=0, padx=6, pady=2)
        self.click_pos_label = ttk.Label(click_frame, text="Click: Same as detection area")
        self.click_pos_label.grid(row=0, column=1, padx=10)

        # Conditions frame
        cond_frame = ttk.LabelFrame(main_frame, text="Conditions", padding=(12, 10))
        cond_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        ttk.Label(cond_frame, text="Type:").grid(row=0, column=0, sticky=tk.W)
        type_frame = ttk.Frame(cond_frame)
        type_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.condition_type = tk.StringVar(value='color')
        ttk.Radiobutton(type_frame, text="Color", variable=self.condition_type, value='color', command=self.on_type_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Text", variable=self.condition_type, value='text', command=self.on_type_change).pack(side=tk.LEFT, padx=10)

        ttk.Label(cond_frame, text="Value:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.value_frame = ttk.Frame(cond_frame)
        self.value_frame.grid(row=1, column=1, padx=5, sticky=(tk.W, tk.E))

        self.color_button = ttk.Button(self.value_frame, text="Pick Color", command=self.pick_color)
        self.color_button_advanced = ttk.Button(self.value_frame, text="Advanced Picker", command=self.pick_color_advanced)
        self.color_label = ttk.Label(self.value_frame, text="No color selected")
        self.text_entry = ttk.Entry(self.value_frame, width=30)

        ttk.Label(cond_frame, text="Comparator:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.comparator = ttk.Combobox(cond_frame, values=['equals', 'contains', 'similar'], state='readonly')
        self.comparator.grid(row=2, column=1, padx=5, sticky=(tk.W, tk.E))
        self.comparator.set('equals')

        ttk.Label(cond_frame, text="Tolerance:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.tolerance = ttk.Scale(cond_frame, from_=0, to=50, orient=tk.HORIZONTAL)
        self.tolerance.grid(row=3, column=1, padx=5, sticky=(tk.W, tk.E))
        self.tolerance.set(10)

        ttk.Button(cond_frame, text="Add Condition", command=self.add_condition).grid(row=4, column=0, columnspan=2, pady=10)

        conditions_frame = ttk.LabelFrame(cond_frame, text="Conditions and Groups")
        conditions_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.unified_tree = ttk.Treeview(conditions_frame, columns=('type', 'details', 'logic'), show='tree headings', height=8)
        self.unified_tree.heading('#0', text='')
        self.unified_tree.heading('type', text='Type')
        self.unified_tree.heading('details', text='Details')
        self.unified_tree.heading('logic', text='Logic')
        self.unified_tree.column('#0', width=30)
        self.unified_tree.column('type', width=100)
        self.unified_tree.column('details', width=300)
        self.unified_tree.column('logic', width=80)

        tree_scrollbar = ttk.Scrollbar(conditions_frame, orient="vertical", command=self.unified_tree.yview)
        self.unified_tree.configure(yscrollcommand=tree_scrollbar.set)
        self.unified_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.tree_context_menu = tk.Menu(self.unified_tree, tearoff=0)
        self.unified_tree.bind("<Button-3>", self.show_tree_context_menu)
        self.unified_tree.bind("<Double-1>", self.on_tree_item_double_click)

        action_buttons = ttk.Frame(conditions_frame)
        action_buttons.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(action_buttons, text="Add Condition", command=self.add_condition).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_buttons, text="New Group", command=self.create_group).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_buttons, text="Edit Selected", command=self.edit_selected_item).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_buttons, text="Remove Selected", command=self.remove_selected_item).pack(side=tk.LEFT, padx=6)

        # Backward-compat hidden widgets
        self.conditions_listbox = tk.Listbox()
        self.groups_listbox = ttk.Treeview(columns=('name', 'logic', 'conditions'))
        self.condition_groups = []

        # Logic frame
        logic_frame = ttk.LabelFrame(main_frame, text="Logic", padding=(12, 10))
        logic_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(logic_frame, text="Rule Logic:").grid(row=0, column=0, sticky=tk.W)
        self.logic = ttk.Combobox(logic_frame, values=['any', 'all', 'n-of'], state='readonly')
        self.logic.grid(row=0, column=1, padx=5)
        self.logic.set('any')
        self.logic.bind('<<ComboboxSelected>>', self.on_logic_change)
        self.n_label = ttk.Label(logic_frame, text="N:")
        self.n_entry = ttk.Entry(logic_frame, width=5)

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=(12, 10))
        settings_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(settings_frame, text="Delay (seconds):").grid(row=0, column=0, sticky=tk.W)
        self.delay = ttk.Combobox(settings_frame, values=['0', '3', '5', '10', '15', '30'], width=8)
        self.delay.grid(row=0, column=1, padx=5)
        self.delay.set('0')
        self.delay.bind('<<ComboboxSelected>>', self._on_delay_change)
        self.delay.bind('<KeyRelease>', self._on_delay_change)
        self.delay.bind('<FocusOut>', self._on_delay_change)
        self.popup_var = tk.BooleanVar(value=True)
        self.popup_checkbox = ttk.Checkbutton(settings_frame, text="Show confirmation popup", variable=self.popup_var)
        self.popup_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        self._on_delay_change()
        ttk.Label(settings_frame, text="Click type:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.click_type = ttk.Combobox(settings_frame, values=['single', 'double', 'right'], width=8, state='readonly')
        self.click_type.grid(row=2, column=1, padx=5)
        self.click_type.set('single')

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=6, column=0, columnspan=2, pady=10)
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=8)
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=8)
        self.logs_button = ttk.Button(control_frame, text="View Logs", command=self.show_logs_window)
        self.logs_button.grid(row=0, column=2, padx=8)

        # Status
        self.status_label = ttk.Label(main_frame, text="Ready", font=("Arial", 10))
        self.status_label.grid(row=7, column=0, columnspan=2, pady=5)

        # Variables
        self.selected_position = None
        self.selected_color = None
        self.selected_area = None
        self.click_position = None
        self.conditions = []
        self.click_count = 0
        
    def select_position(self):
        """Let user select a position on screen with real-time feedback"""
        # Hide the main window temporarily  
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Position Selection", 
                              "Move your mouse to the desired position and click OK.\n"
                              "The mouse coordinates will be captured.")
            
            # Get current mouse position
            self.selected_position = pyautogui.position()
            self.selected_area = None  # Clear area selection when selecting point
            
            # Also capture the color at this position for reference
            screenshot = pyautogui.screenshot()
            pixel_color = screenshot.getpixel(self.selected_position)
            
            self.pos_label.config(text=f"Position: {self.selected_position} (Color: RGB{pixel_color[:3]})")
            
            # Log position selection
            self.logger.log_action("SELECT_POSITION", {
                "position": self.selected_position,
                "reference_color": pixel_color[:3]
            }, success=True)
            
            messagebox.showinfo("Position Captured", 
                              f"Position {self.selected_position} captured!\n"
                              f"Reference color: RGB{pixel_color[:3]}")
            
        except Exception as e:
            self.logger.log_error(f"Error selecting position: {str(e)}", "ui", e)
            messagebox.showerror("Error", f"Failed to select position: {str(e)}")
        
        finally:
            # Restore the main window
            self.root.deiconify()
    
    def select_area(self):
        """Let user select an area on screen by clicking two points"""
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Area Selection", 
                              "Click the TOP-LEFT corner of the area first.")
            
            # Get first point (top-left)
            x1, y1 = pyautogui.position()
            
            messagebox.showinfo("Area Selection", 
                              f"Top-left: ({x1}, {y1})\n"
                              f"Now click the BOTTOM-RIGHT corner.")
            
            # Get second point (bottom-right)
            x2, y2 = pyautogui.position()
            
            # Ensure we have the correct order (top-left to bottom-right)
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            self.selected_area = (x1, y1, x2, y2)
            self.selected_position = None  # Clear point selection
            
            width = x2 - x1
            height = y2 - y1
            
            self.pos_label.config(text=f"Area: ({x1},{y1}) to ({x2},{y2}) [{width}x{height}]")
            
            # Log area selection
            self.logger.log_action("SELECT_AREA", {
                "area": self.selected_area,
                "size": f"{width}x{height}"
            }, success=True)
            
            messagebox.showinfo("Area Captured", 
                              f"Area selected: {width}x{height} pixels\n"
                              f"Top-left: ({x1}, {y1})\n"
                              f"Bottom-right: ({x2}, {y2})")
            
        except Exception as e:
            self.logger.log_error(f"Error selecting area: {str(e)}", "ui", e)
            messagebox.showerror("Error", f"Failed to select area: {str(e)}")
        
        finally:
            self.root.deiconify()
    
    def select_click_position(self):
        """Let user select a separate click position"""
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Click Position", 
                              "Select where you want to click when conditions are met.")
            
            self.click_position = pyautogui.position()
            
            self.click_pos_label.config(text=f"Click: {self.click_position}")
            
            # Log click position selection
            self.logger.log_action("SELECT_CLICK_POSITION", {
                "position": self.click_position
            }, success=True)
            
            messagebox.showinfo("Click Position Set", 
                              f"Click position set to: {self.click_position}")
            
        except Exception as e:
            self.logger.log_error(f"Error selecting click position: {str(e)}", "ui", e)
            messagebox.showerror("Error", f"Failed to select click position: {str(e)}")
        
        finally:
            self.root.deiconify()
        
    def on_type_change(self, event=None):
        """Handle condition type change"""
        # Clear previous widgets
        for widget in self.value_frame.winfo_children():
            widget.grid_remove()
            
        current_type = self.condition_type.get()
        if current_type == 'color':
            self.color_button.grid(row=0, column=0, padx=2)
            self.color_button_advanced.grid(row=0, column=1, padx=2)
            self.color_label.grid(row=0, column=2, padx=5)
        else:  # text
            self.text_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
            
    def pick_color(self):
        """Capture color from screen at current mouse position"""
        # Hide the main window temporarily
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Color Picker", 
                              "Move your mouse to the desired position and click OK.\n"
                              "The color at your mouse position will be captured.")
            
            # Get current mouse position
            mouse_x, mouse_y = pyautogui.position()
            
            # Capture the color at mouse position
            screenshot = pyautogui.screenshot()
            pixel_color = screenshot.getpixel((mouse_x, mouse_y))
            
            # Store RGB values (ignore alpha if present)
            self.selected_color = tuple(pixel_color[:3])
            self.color_label.config(text=f"RGB: {self.selected_color} at ({mouse_x}, {mouse_y})")
            
            # Log color selection with position info
            self.logger.log_action("PICK_COLOR", {
                "color": self.selected_color, 
                "position": (mouse_x, mouse_y)
            }, success=True)
            
            messagebox.showinfo("Color Captured", 
                              f"Captured color RGB{self.selected_color} at position ({mouse_x}, {mouse_y})")
            
        except Exception as e:
            self.logger.log_error(f"Error capturing color: {str(e)}", "ui", e)
            messagebox.showerror("Error", f"Failed to capture color: {str(e)}")
        
        finally:
            # Restore the main window
            self.root.deiconify()
    
    def pick_color_advanced(self):
        """Advanced color picker with real-time preview"""
        # Create a new window for advanced color picking
        picker_window = tk.Toplevel(self.root)
        picker_window.title("Advanced Color Picker")
        picker_window.geometry("400x300")
        picker_window.transient(self.root)
        
        # Variables for real-time updates
        position_var = tk.StringVar(value="Move mouse to see position...")
        color_var = tk.StringVar(value="RGB: (0, 0, 0)")
        
        # UI elements
        ttk.Label(picker_window, text="Real-time Color Picker", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(picker_window, textvariable=position_var).pack(pady=5)
        ttk.Label(picker_window, textvariable=color_var, font=("Courier", 12)).pack(pady=5)
        
        # Color preview canvas
        canvas = tk.Canvas(picker_window, width=100, height=50, bg="white")
        canvas.pack(pady=10)
        
        # Control buttons
        button_frame = ttk.Frame(picker_window)
        button_frame.pack(pady=10)
        
        def update_preview():
            """Update real-time preview"""
            try:
                # Get current mouse position
                x, y = pyautogui.position()
                position_var.set(f"Position: ({x}, {y})")
                
                # Get color at mouse position
                screenshot = pyautogui.screenshot()
                rgb = screenshot.getpixel((x, y))[:3]
                color_var.set(f"RGB: {rgb}")
                
                # Update color preview
                hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                canvas.configure(bg=hex_color)
                
            except Exception:
                pass  # Ignore errors during preview
            
            # Schedule next update
            if picker_window.winfo_exists():
                picker_window.after(100, update_preview)
        
        def capture_current_color():
            """Capture the current color and close picker"""
            try:
                x, y = pyautogui.position()
                screenshot = pyautogui.screenshot()
                rgb = screenshot.getpixel((x, y))[:3]
                
                self.selected_color = rgb
                self.color_label.config(text=f"RGB: {self.selected_color} at ({x}, {y})")
                
                # Log color selection
                self.logger.log_action("PICK_COLOR_ADVANCED", {
                    "color": self.selected_color, 
                    "position": (x, y)
                }, success=True)
                
                picker_window.destroy()
                messagebox.showinfo("Color Captured", 
                                  f"Captured RGB{self.selected_color} at ({x}, {y})")
                
            except Exception as e:
                self.logger.log_error(f"Error in advanced color picker: {str(e)}", "ui", e)
                messagebox.showerror("Error", f"Failed to capture color: {str(e)}")
        
        ttk.Button(button_frame, text="Capture This Color", command=capture_current_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=picker_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Start real-time updates
        update_preview()
        
        # Instructions
        instructions = tk.Text(picker_window, height=4, width=50, wrap=tk.WORD)
        instructions.pack(pady=10, padx=20)
        instructions.insert(tk.END, 
            "Instructions:\n"
            "1. Move your mouse over the target color\n"
            "2. Watch the real-time preview above\n"
            "3. Click 'Capture This Color' when ready")
        instructions.config(state=tk.DISABLED)
            
    def add_condition(self):
        """Add a new condition"""
        # Check if we have either a position or area selected
        if not self.selected_position and not self.selected_area:
            messagebox.showerror("Error", "Please select a position or area first")
            self.logger.log_error("Failed to add condition: No position/area selected", "ui")
            return
            
        if not self.condition_type.get():
            messagebox.showerror("Error", "Please select a condition type")
            self.logger.log_error("Failed to add condition: No condition type selected", "ui")
            return
            
        if self.condition_type.get() == 'color' and not self.selected_color:
            messagebox.showerror("Error", "Please pick a color")
            self.logger.log_error("Failed to add condition: No color selected", "ui")
            return
            
        if self.condition_type.get() == 'text' and not self.text_entry.get():
            messagebox.showerror("Error", "Please enter text to detect")
            self.logger.log_error("Failed to add condition: No text entered", "ui")
            return
            
        value = self.selected_color if self.condition_type.get() == 'color' else self.text_entry.get()
        
        # Use area if selected, otherwise use position
        detection_position = self.selected_area if self.selected_area else self.selected_position
        
        condition = Condition(
            type=self.condition_type.get(),
            position=detection_position,
            value=value,
            comparator=self.comparator.get(),
            tolerance=int(self.tolerance.get())
        )
        
        self.conditions.append(condition)
        
        # Create a more descriptive condition string
        position_desc = ""
        if len(condition.position) == 4:
            x1, y1, x2, y2 = condition.position
            width, height = x2-x1, y2-y1
            position_desc = f"Area: ({x1},{y1}) to ({x2},{y2}) [{width}x{height}]"
        else:
            x, y = condition.position
            # position_desc = f"Point({x},{y})"  # unused
            
        # Create friendly descriptions for each element
    # type_desc = "📊 Color" if condition.type == "color" else "📝 Text"  # unused
        
        value_desc = ""
        if condition.type == "color":
            if isinstance(condition.value, tuple) and len(condition.value) == 3:
                r, g, b = condition.value
                value_desc = f"RGB({r},{g},{b})"
            else:
                value_desc = str(condition.value)
        elif condition.type == "text":
            # Truncate text if too long
            if len(condition.value) > 20:
                value_desc = f"\"{condition.value[:17]}...\""
            else:
                value_desc = f"\"{condition.value}\""
        else:
            pass
        
        # Simplified comparison description
        comp_desc = ""
        if condition.type == "color":
            if condition.comparator == "equals":
                comp_desc = "exactly matches"
            elif condition.comparator == "similar":
                comp_desc = f"is similar to (tolerance: {condition.tolerance})"
        else:  # Text
            if condition.comparator == "equals":
                comp_desc = "exactly matches"
            elif condition.comparator == "contains":
                comp_desc = "contains"
            elif condition.comparator == "similar":
                pass
        
        # We already added the condition earlier, no need to append again
        # Just update the display to show the new condition
        self.update_conditions_display()
        
        # Log the condition addition
        self.logger.log_action("ADD_CONDITION", {
            "type": condition.type,
            "position": condition.position,
            "value": str(condition.value),
            "comparator": condition.comparator,
            "tolerance": condition.tolerance
        }, success=True)
        
    def _conditions_equal(self, cond1, cond2):
        """Compare two conditions for equality"""
        # Two conditions are equal if they have the same type, position, value, and comparator
        return (cond1.type == cond2.type and 
                cond1.position == cond2.position and
                cond1.value == cond2.value and 
                cond1.comparator == cond2.comparator and
                cond1.tolerance == cond2.tolerance)
    
    def _condition_in_list(self, condition, condition_list):
        """Check if a condition is in a list using our custom equality check"""
        for i, c in enumerate(condition_list):
            if self._conditions_equal(condition, c):
                # If they're the same condition but different objects,
                # make sure they reference the same object
                if id(condition) != id(c):
                    condition_list[i] = condition  # Update the reference in the list
                return True
        return False
    
    def update_conditions_display(self):
        """Update the tree view to display all conditions and groups"""
        # First, make sure the main conditions list contains all conditions
        self._ensure_conditions_consistency()
        
        # Clear the tree view
        for item in self.unified_tree.get_children():
            self.unified_tree.delete(item)
        
        # Also clear the hidden compatibility listbox
        self.conditions_listbox.delete(0, tk.END)
        
        # Track which conditions are in groups
        conditions_in_groups = []
        for group in self.condition_groups:
            for condition in group.conditions:
                if not self._condition_in_list(condition, conditions_in_groups):
                    conditions_in_groups.append(condition)
        
        # First add all the groups as parent items, except 'Default Group'
        group_display_index = 0
        for i, group in enumerate(self.condition_groups):
            if group.name == "Default Group":
                # Show these as standalone, not as a group
                for condition in group.conditions:
                    if not self._condition_in_list(condition, conditions_in_groups):
                        conditions_in_groups.append(condition)
                continue
            # Format the logic text
            if group.logic == "all":
                logic_text = "ALL (AND)"
            elif group.logic == "any":
                logic_text = "ANY (OR)"
            elif group.logic == "n-of" and group.n is not None:
                logic_text = f"{group.n} of {len(group.conditions)}"
            else:
                logic_text = group.logic

            # Add the group as a parent item
            group_id = f"group_{group_display_index}"
            group_display_index += 1
            self.unified_tree.insert('', 'end', group_id, text='▼', 
                                  values=('Group', group.name, logic_text),
                                  tags=('group',))

            # Add conditions within this group
            for j, condition in enumerate(group.conditions):
                # Format condition description
                condition_text = self._format_condition_description(condition)

                # Add as child of group
                self.unified_tree.insert(group_id, 'end', f"{group_id}_cond_{j}", text='',
                                     values=('Condition', condition_text, ''),
                                     tags=('group_condition',))
        
        # Then add standalone conditions (those not in any group)
        standalone_conditions = []
        
        # Debug information
        condition_ids = [id(c) for c in self.conditions]
        group_condition_ids = [id(c) for c in conditions_in_groups]
        
        print(f"All condition IDs: {condition_ids}")
        print(f"Group condition IDs: {group_condition_ids}")
        
        for condition in self.conditions:
            # For each condition in the main list, check if it's in any group
            condition_in_group = False
            for group_condition in conditions_in_groups:
                if id(condition) == id(group_condition) or self._conditions_equal(condition, group_condition):
                    condition_in_group = True
                    break
                    
            if not condition_in_group:
                standalone_conditions.append(condition)
                
        print(f"Standalone conditions: {len(standalone_conditions)}, Total conditions: {len(self.conditions)}, In groups: {len(conditions_in_groups)}")
                
        for i, condition in enumerate(standalone_conditions):
            # Format condition description
            condition_text = self._format_condition_description(condition)
            
            # Add as standalone item
            self.unified_tree.insert('', 'end', f"cond_{i}", text='',
                                values=('Condition', condition_text, ''),
                                tags=('condition',))
            
            # Also add to the hidden listbox for backward compatibility
            self.conditions_listbox.insert(tk.END, condition_text)
    
    def _ensure_conditions_consistency(self):
        """Ensure that self.conditions only contains standalone conditions (not in any group)."""
        print("Starting condition consistency check...")
        print(f"Before: Main conditions: {len(self.conditions)}, Group conditions: {sum(len(g.conditions) for g in self.condition_groups)}")

        # Build a set of all group condition ids
        group_condition_ids = set()
        for group in self.condition_groups:
            for group_condition in group.conditions:
                group_condition_ids.add(id(group_condition))

        # Remove any condition from self.conditions that is present in any group
        original_conditions = self.conditions[:]
        self.conditions = [cond for cond in original_conditions if id(cond) not in group_condition_ids]

        # Optionally, update group references to use the same object as in self.conditions if needed
        # (not strictly necessary if conditions are only in one place)

        print(f"After: Main conditions: {len(self.conditions)}, Group conditions: {sum(len(g.conditions) for g in self.condition_groups)}")
                
        # Configure tag appearance with more distinctive colors
        self.unified_tree.tag_configure('group', background='#d0d0ff', font=('Arial', 9, 'bold'))
        self.unified_tree.tag_configure('group_condition', background='#e0e0ff')
        self.unified_tree.tag_configure('condition', background='white')
        
    def _format_condition_description(self, condition):
        """Format a condition into a readable description string"""
        # Position description
        if len(condition.position) == 4:
            x1, y1, x2, y2 = condition.position
            width, height = x2-x1, y2-y1
            position_desc = f"Area: ({x1},{y1}) to ({x2},{y2}) [{width}x{height}]"
        else:
            x, y = condition.position
            position_desc = f"Point({x},{y})"
            
        # Type icon
        type_desc = "📊 Color" if condition.type == "color" else "📝 Text"
        
        # Value description
        if condition.type == "color":
            if isinstance(condition.value, tuple) and len(condition.value) == 3:
                r, g, b = condition.value
                value_desc = f"RGB({r},{g},{b})"
            else:
                value_desc = str(condition.value)
        else:  # Text
            if len(condition.value) > 20:
                value_desc = f"\"{condition.value[:17]}...\""
            else:
                value_desc = f"\"{condition.value}\""
        
        # Comparison description
        if condition.type == "color":
            if condition.comparator == "equals":
                comp_desc = "exactly matches"
            elif condition.comparator == "similar":
                comp_desc = f"is similar to (tolerance: {condition.tolerance})"
            else:
                comp_desc = condition.comparator
        else:  # Text
            if condition.comparator == "equals":
                comp_desc = "exactly matches"
            elif condition.comparator == "contains":
                comp_desc = "contains"
            elif condition.comparator == "similar":
                comp_desc = "is similar to"
            else:
                comp_desc = condition.comparator
                
        # Format the full condition string
        return f"{type_desc}: {value_desc} {comp_desc} at {position_desc}"
                
    def edit_condition(self):
        """Edit selected condition"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a condition to edit")
            return
            
        index = selection[0]
        if index >= len(self.conditions):
            return
            
        condition_to_edit = self.conditions[index]
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Condition")
        dialog.geometry("500x400")
        dialog.minsize(500, 400)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure grid
        dialog.columnconfigure(0, weight=1)
        dialog.columnconfigure(1, weight=2)
        
        # Type
        ttk.Label(dialog, text="Type:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        type_var = tk.StringVar(value=condition_to_edit.type)
        type_frame = ttk.Frame(dialog)
        type_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        ttk.Radiobutton(type_frame, text="Color", variable=type_var, value="color").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Text", variable=type_var, value="text").pack(side=tk.LEFT, padx=10)
        
        # Position (display only, can't edit position)
        ttk.Label(dialog, text="Position:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        if len(condition_to_edit.position) == 4:
            x1, y1, x2, y2 = condition_to_edit.position
            position_text = f"Area: ({x1},{y1}) to ({x2},{y2})"
        else:
            x, y = condition_to_edit.position
            position_text = f"Point({x},{y})"
            
        ttk.Label(dialog, text=position_text).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Value
        ttk.Label(dialog, text="Value:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        value_var = tk.StringVar()
        if condition_to_edit.type == "color":
            if isinstance(condition_to_edit.value, tuple) and len(condition_to_edit.value) == 3:
                r, g, b = condition_to_edit.value
                value_var.set(f"RGB({r},{g},{b})")
                # Value is display-only for colors
                ttk.Label(dialog, text=value_var.get()).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
            else:
                value_var.set(str(condition_to_edit.value))
                ttk.Label(dialog, text=value_var.get()).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        else:
            value_var.set(condition_to_edit.value)
            ttk.Entry(dialog, textvariable=value_var).grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        # Comparator
        ttk.Label(dialog, text="Comparator:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        
        comparator_var = tk.StringVar(value=condition_to_edit.comparator)
        comparator_options = ['equals', 'contains', 'similar']
        comparator_combo = ttk.Combobox(dialog, textvariable=comparator_var, values=comparator_options, state='readonly')
        comparator_combo.grid(row=3, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        # Tolerance (for color)
        ttk.Label(dialog, text="Tolerance:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        
        tolerance_var = tk.IntVar(value=condition_to_edit.tolerance if condition_to_edit.tolerance else 10)
        tolerance_scale = ttk.Scale(dialog, from_=0, to=50, orient=tk.HORIZONTAL, variable=tolerance_var)
        tolerance_scale.grid(row=4, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        ttk.Label(dialog, textvariable=tolerance_var).grid(row=4, column=2, padx=5, pady=10, sticky=tk.W)
        
        # Save function
        def save_edited_condition():
            # Update condition with new values
            condition_to_edit.type = type_var.get()
            if condition_to_edit.type == "text":
                condition_to_edit.value = value_var.get()
            # Don't update color value as it can't be edited in UI
            condition_to_edit.comparator = comparator_var.get()
            condition_to_edit.tolerance = tolerance_var.get()
            
            # Update displays
            self.update_conditions_display()
            self.update_groups_display()
            
            # Log the edit
            self.logger.log_action("EDIT_CONDITION", {
                "type": condition_to_edit.type,
                "position": condition_to_edit.position,
                "value": str(condition_to_edit.value),
                "comparator": condition_to_edit.comparator,
                "tolerance": condition_to_edit.tolerance
            }, success=True)
            
            dialog.destroy()
            
        # Add buttons
        ttk.Button(dialog, text="Cancel", 
                  command=dialog.destroy).grid(row=5, column=0, padx=10, pady=20)
                  
        ttk.Button(dialog, text="Save Changes", 
                  command=save_edited_condition).grid(row=5, column=1, padx=10, pady=20)
        
    def remove_condition(self):
        """Remove selected condition"""
        selection = self.conditions_listbox.curselection()
        if selection:
            index = selection[0]
            removed_condition = self.conditions[index]
            
            # Check if condition is in a group and remove it from there too
            for group in self.condition_groups:
                # Need to find the matching condition in the group
                for i, group_condition in enumerate(group.conditions):
                    if self._conditions_equal(removed_condition, group_condition):
                        group.conditions.pop(i)
                        break
            
            # Remove from main list
            del self.conditions[index]
            
            # Update both displays
            self.update_conditions_display()
            self.update_groups_display()
            
            # Log condition removal
            self.logger.log_action("REMOVE_CONDITION", {
                "type": removed_condition.type,
                "position": removed_condition.position
            }, success=True)
            
    def on_logic_change(self, event=None):
        """Handle logic change"""
        if self.logic.get() == 'n-of':
            self.n_label.grid(row=0, column=2, padx=5)
            self.n_entry.grid(row=0, column=3, padx=5)
        else:
            self.n_label.grid_remove()
            self.n_entry.grid_remove()
            
    def start_monitoring(self):
        """Start the autoclicker monitoring"""
        # Combine all conditions and groups for validation
        total_conditions = len(self.conditions) + sum(len(g.conditions) for g in self.condition_groups)
        if total_conditions == 0:
            messagebox.showerror("Error", "Please add at least one condition or group")
            self.logger.log_error("Failed to start monitoring: No conditions or groups added", "ui")
            return

        # Reset click counter for new monitoring session
        self.click_count = 0

        # Determine click position - use separate click position if set, otherwise use first standalone or group condition position
        click_pos = (0, 0)
        if self.click_position:
            click_pos = self.click_position
        elif self.conditions:
            first_pos = self.conditions[0].position
            if len(first_pos) == 4:
                x1, y1, x2, y2 = first_pos
                click_pos = ((x1 + x2) // 2, (y1 + y2) // 2)
            else:
                click_pos = first_pos
        elif self.condition_groups and self.condition_groups[0].conditions:
            first_pos = self.condition_groups[0].conditions[0].position
            if len(first_pos) == 4:
                x1, y1, x2, y2 = first_pos
                click_pos = ((x1 + x2) // 2, (y1 + y2) // 2)
            else:
                click_pos = first_pos

        # Build the rule with both standalone and group conditions
        rule = Rule(
            click_position=click_pos,
            condition_groups=self.condition_groups.copy(),
            group_logic=self.logic.get() if self.logic.get() else 'any',
            conditions=self.conditions.copy() if self.conditions else None,
            logic=None,  # Not used in new format
            n=None      # Not used in new format
        )

        self.config = Config(
            rules=[rule],
            delay=int(self.delay.get()) if self.delay.get() else 0,
            popup=self.popup_var.get()
        )

        # Create and start monitor
        self.monitor = ScreenMonitor(self.config)
        self.monitor.set_rule_matched_callback(self.on_rule_matched)

        if self.monitor.start_monitoring():
            self.status_label.config(text="Monitoring active...")
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            # Log successful monitoring start
            self.logger.log_monitoring("START", rule_count=len(self.config.rules), success=True)
            
            # Get total condition count (handling both new and old rule structures)
            if hasattr(rule, 'condition_groups') and rule.condition_groups:
                total_conditions = sum(len(group.conditions) for group in rule.condition_groups)
                logic = f"{rule.group_logic} of groups"
            elif hasattr(rule, 'conditions') and rule.conditions:
                total_conditions = len(rule.conditions)
                logic = rule.logic
            else:
                total_conditions = 0
                logic = "unknown"
                
            self.logger.log_action("START_MONITORING", {
                "conditions": total_conditions,
                "logic": logic,
                "delay": self.config.delay,
                "popup": self.config.popup,
                "click_type": self.click_type.get()
            }, success=True)
        else:
            messagebox.showerror("Error", "Failed to start monitoring")
            self.logger.log_monitoring("START", rule_count=len(self.config.rules), success=False)
        
    def stop_monitoring(self):
        """Stop the autoclicker monitoring"""
        if self.monitor:
            self.monitor.stop_monitoring()
            
        # Cancel any active delay/popup
        if self.delay_popup_manager:
            self.delay_popup_manager.cancel_current_action()
            
        self.status_label.config(text="Monitoring stopped")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        # Log monitoring stop
        self.logger.log_monitoring("STOP", success=True)
        self.logger.log_action("STOP_MONITORING", {}, success=True)
        
    def on_rule_matched(self, rule):
        """Callback when a rule is matched"""
        # Log rule match - handle both new and old rule structures
        if hasattr(rule, 'condition_groups') and rule.condition_groups:
            # New structure with condition groups
            total_conditions = sum(len(group.conditions) for group in rule.condition_groups)
            logic = rule.group_logic
            # Get position from click_position or first condition in first group
            if hasattr(rule, 'click_position') and rule.click_position:
                position = rule.click_position
            elif rule.condition_groups and rule.condition_groups[0].conditions:
                position = rule.condition_groups[0].conditions[0].position
                # Handle area position
                if len(position) == 4:
                    x1, y1, x2, y2 = position
                    position = ((x1 + x2) // 2, (y1 + y2) // 2)
            else:
                position = (0, 0)
        elif hasattr(rule, 'conditions') and rule.conditions:
            # Old structure with direct conditions
            total_conditions = len(rule.conditions)
            logic = rule.logic
            position = rule.conditions[0].position if rule.conditions else (0, 0)
        else:
            total_conditions = 0
            logic = "unknown"
            position = (0, 0)
            
        self.logger.log_rule_match(logic, total_conditions, position)
        
        # Get current config settings
        delay_seconds = self.config.delay
        show_popup = self.config.popup
        
        # Always allow popup even with zero delay (acts as immediate confirmation dialog)
        if show_popup:
            if delay_seconds > 0:
                self.status_label.config(text="🎯 Rule matched! Showing confirmation & countdown...")
            else:
                self.status_label.config(text="🎯 Rule matched! Awaiting user confirmation...")
        else:
            if delay_seconds > 0:
                self.status_label.config(text=f"🎯 Rule matched! Waiting {delay_seconds}s before executing...")
            else:
                self.status_label.config(text="🎯 Rule matched! Executing immediately...")
        
        # Create rule info string for display
        if hasattr(rule, 'condition_groups') and rule.condition_groups:
            group_count = len(rule.condition_groups)
            total_conditions = sum(len(group.conditions) for group in rule.condition_groups)
            rule_info = f"{rule.group_logic} of {group_count} groups with {total_conditions} total condition(s)"
        elif hasattr(rule, 'conditions') and rule.conditions:
            rule_info = f"{rule.logic} logic with {len(rule.conditions)} condition(s)"
        else:
            rule_info = "Rule matched"
        
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
        self.status_label.config(text="Executing click action...")
        
        try:
            # Get the selected click type
            click_type = self.click_type.get() if hasattr(self, 'click_type') else 'single'
            
            # Perform the actual mouse click using MouseClicker
            success = self.mouse_clicker.click_for_rule(rule, click_type=click_type)
            
            # Log the click attempt
            # Use the new click_position if available, otherwise fallback to first condition
            if hasattr(rule, 'click_position') and rule.click_position:
                position = rule.click_position
            else:
                position = rule.conditions[0].position if rule.conditions else (0, 0)
            self.logger.log_click(position, click_type, success)
            
            if success:
                self.click_count += 1
                self.status_label.config(text=f"Click #{self.click_count} executed successfully!")
                # Removed success popup to avoid interference with continuous clicking
                print(f"✅ Click #{self.click_count} executed successfully at {position}")
            else:
                self.status_label.config(text="Click failed!")
                # Only show error popup for failures (user needs to know about failures)
                # Create rule info string for error display
                if hasattr(rule, 'condition_groups') and rule.condition_groups:
                    group_count = len(rule.condition_groups)
                    total_conditions = sum(len(group.conditions) for group in rule.condition_groups)
                    rule_desc = f"{rule.group_logic} of {group_count} groups with {total_conditions} total condition(s)"
                elif hasattr(rule, 'conditions') and rule.conditions:
                    rule_desc = f"{rule.logic} logic with {len(rule.conditions)} condition(s)"
                else:
                    rule_desc = "Rule matched"
                    
                messagebox.showerror("Error", 
                                   f"❌ Failed to execute mouse click!\n"
                                   f"Rule: {rule_desc}")
                
        except Exception as e:
            self.status_label.config(text="Click error!")
            self.logger.log_error(f"Error executing click: {str(e)}", "ui", e)
            messagebox.showerror("Error", f"❌ Error executing click: {str(e)}")
        
        # Reset status after a delay
        self.root.after(2000, lambda: self.status_label.config(text=f"Monitoring active... (clicks: {self.click_count})"))
        
        # Resume monitoring after click action is complete
        if self.monitor:
            self.monitor.resume_monitoring()
    
    def _on_delay_change(self, event=None):
        """Handle delay field changes to update popup checkbox state"""
        try:
            delay_value = int(self.delay.get() or '0')
            
            if delay_value == 0:
                # Grey out popup checkbox when delay is 0
                self.popup_checkbox.config(state='disabled')
                self.popup_var.set(False)  # Uncheck the checkbox
                # Add tooltip-like text
                self.popup_checkbox.config(text="Show confirmation popup (disabled - no delay)")
            else:
                # Enable popup checkbox when delay > 0
                self.popup_checkbox.config(state='normal')
                self.popup_var.set(True)  # Check the checkbox
                self.popup_checkbox.config(text="Show confirmation popup")
                
        except ValueError:
            # Invalid delay value, treat as 0
            self.popup_checkbox.config(state='disabled')
            self.popup_var.set(False)
            self.popup_checkbox.config(text="Show confirmation popup (disabled - invalid delay)")
    
    def on_action_cancelled(self):
        """Callback when user cancels the action"""
        self.status_label.config(text="❌ Action cancelled by user")
        
        # Log the cancellation
        self.logger.log_action("CANCEL_ACTION", {}, success=True)
        
        print("❌ User cancelled the click action")
        
        # Resume monitoring after cancellation
        if self.monitor:
            self.monitor.resume_monitoring()
        
        # Reset status after a delay
        self.root.after(2000, lambda: self.status_label.config(text=f"Monitoring active... (clicks: {self.click_count})"))
        
    def show_logs_window(self):
        """Show the logs viewing window"""
        self.logger.log_action("OPEN_LOGS", {}, success=True)
        
        logs_window = tk.Toplevel(self.root)
        logs_window.title("Autoclicker Logs")
        logs_window.geometry("800x600")
        logs_window.transient(self.root)
        
        # Create notebook for different log types
        notebook = ttk.Notebook(logs_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log types
        log_types = {
            "Actions": "action",
            "Errors": "error", 
            "All Logs": "main"
        }
        
        log_texts = {}
        
        for tab_name, log_type in log_types.items():
            # Create frame for this log type
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=tab_name)
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            log_texts[log_type] = text_widget
            
            # Add control buttons for each tab
            control_frame = ttk.Frame(frame)
            control_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Button(control_frame, text="Refresh", 
                      command=lambda lt=log_type: self.refresh_logs(log_texts[lt], lt)).pack(side=tk.LEFT, padx=5)
            ttk.Button(control_frame, text="Clear", 
                      command=lambda lt=log_type: self.clear_log_type(lt)).pack(side=tk.LEFT, padx=5)
            ttk.Button(control_frame, text="Export", 
                      command=lambda lt=log_type: self.export_log_type(lt)).pack(side=tk.LEFT, padx=5)
        
        # Load initial logs
        for log_type, text_widget in log_texts.items():
            self.refresh_logs(text_widget, log_type)
        
        # Add statistics panel
        stats_frame = ttk.LabelFrame(logs_window, text="Log Statistics", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.update_log_stats(stats_frame)
        
    def refresh_logs(self, text_widget: tk.Text, log_type: str):
        """Refresh logs in the text widget"""
        try:
            logs = self.logger.get_recent_logs(log_type, lines=500)
            
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            
            if logs:
                text_widget.insert(tk.END, "\n".join(logs))
            else:
                text_widget.insert(tk.END, f"No {log_type} logs available.")
            
            text_widget.config(state=tk.DISABLED)
            text_widget.see(tk.END)  # Scroll to bottom
            
        except Exception as e:
            self.logger.log_error(f"Failed to refresh {log_type} logs", "ui", e)
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, f"Error loading logs: {str(e)}")
            text_widget.config(state=tk.DISABLED)
    
    def clear_log_type(self, log_type: str):
        """Clear logs of specified type"""
        result = messagebox.askyesno("Confirm Clear", 
                                   f"Are you sure you want to clear all {log_type} logs?\n"
                                   "This action cannot be undone.")
        if result:
            try:
                self.logger.clear_logs(log_type)
                messagebox.showinfo("Success", f"{log_type} logs cleared successfully!")
                self.logger.log_action("CLEAR_LOGS", {"type": log_type}, success=True)
            except Exception as e:
                self.logger.log_error(f"Failed to clear {log_type} logs", "ui", e)
                messagebox.showerror("Error", f"Failed to clear logs: {str(e)}")
    
    def export_log_type(self, log_type: str):
        """Export logs of specified type"""
        export_dir = filedialog.askdirectory(title=f"Select directory to export {log_type} logs")
        if export_dir:
            try:
                success = self.logger.export_logs(export_dir, log_type)
                if success:
                    messagebox.showinfo("Success", f"{log_type} logs exported successfully to {export_dir}")
                    self.logger.log_action("EXPORT_LOGS", {"type": log_type, "path": export_dir}, success=True)
                else:
                    messagebox.showerror("Error", "Failed to export logs")
            except Exception as e:
                self.logger.log_error(f"Failed to export {log_type} logs", "ui", e)
                messagebox.showerror("Error", f"Failed to export logs: {str(e)}")
    
    def update_log_stats(self, parent_frame: ttk.Frame):
        """Update log statistics display"""
    # stats = self.logger.get_log_stats()
        # ...existing code for updating the UI with stats...
    
    def save_config(self):
        """Save the current configuration to a file"""
        # Create a rule from the current UI state
        if not self._create_rule_from_ui():
            return
            
        # Get file path with default name autoclicker_[date]_[time].json
        import datetime
        now = datetime.datetime.now()
        today_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        
        # Use config name if provided, else default
        config_name = self.config_name_var.get().strip()
        if config_name:
            # Clean up name for filename (remove spaces and special chars)
            import re
            safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', config_name)
            default_name = f"{safe_name}.json"
        else:
            default_name = f"autoclicker_{today_str}_{time_str}.json"
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Autoclicker Config", "*.json"), ("All Files", "*.*")],
            title="Save Configuration",
            initialfile=default_name
        )
        
        if not file_path:
            return
            
        try:
            # Convert config to dictionary
            config_dict = self.config.to_dict()
            
            # Save the name in the config if provided, or derive from filename
            import os
            filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            if config_name:
                config_dict['name'] = config_name
            else:
                # If no name was provided, use the chosen filename as the name
                config_dict['name'] = filename_without_ext
                # Also update the UI field
                self.config_name_var.set(filename_without_ext)
            
            # Write to file
            with open(file_path, 'w') as file:
                json.dump(config_dict, file, indent=4)
                
            self.logger.log_info(f"Configuration saved to {file_path}", "ui")
            messagebox.showinfo("Save Configuration", f"Configuration saved successfully to {file_path}")
        except Exception as e:
            self.logger.log_error(f"Failed to save configuration: {e}", "ui")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load a configuration from a file"""
        # Get file path
        file_path = filedialog.askopenfilename(
            filetypes=[("Autoclicker Config", "*.json"), ("All Files", "*.*")],
            title="Open Configuration"
        )
        
        if not file_path:
            return
            
        try:
            # Read the file
            with open(file_path, 'r') as file:
                config_dict = json.load(file)
                
            # Convert dictionary to Config object
            config = Config.from_dict(config_dict)
            
            # Apply the configuration
            self._apply_config(config)

            # Set the configuration name from the file name or saved name
            import os
            filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            
            # If a name is present in the config, use it, otherwise use filename
            if 'name' in config_dict and config_dict['name']:
                self.config_name_var.set(config_dict['name'])
            else:
                # Use filename without extension as the config name
                self.config_name_var.set(filename_without_ext)
                
            self.logger.log_info(f"Configuration loaded from {file_path}", "ui")
            messagebox.showinfo("Load Configuration", f"Configuration loaded successfully from {file_path}")
        except Exception as e:
            self.logger.log_error(f"Failed to load configuration: {e}", "ui")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def _create_rule_from_ui(self):
        """Create a rule from the current UI state"""
        # Check for required fields
        if not self.condition_groups and not self.conditions:
            messagebox.showerror("Error", "Please add at least one condition or group")
            return False
            
        # Get the click position
        click_position = self.selected_click_position
        if not click_position:
            # Use detection position if click position not specified
            if self.selected_area:
                # For area, use the center point
                x1, y1, x2, y2 = self.selected_area
                click_position = ((x1 + x2) // 2, (y1 + y2) // 2)
            elif self.selected_position:
                click_position = self.selected_position
            else:
                messagebox.showerror("Error", "Please set a position first")
                return False
                
        # Always nest everything inside a single 'Default Group' for saving
        # Merge all standalone conditions and all 'Default Group' group conditions into one
        merged_default_conditions = self.conditions.copy() if self.conditions else []
        other_groups = []
        for group in (self.condition_groups or []):
            if group.name == "Default Group":
                merged_default_conditions.extend(group.conditions)
            else:
                other_groups.append(group)
        all_groups = []
        if merged_default_conditions:
            default_group = ConditionGroup(
                conditions=merged_default_conditions,
                logic="all",
                name="Default Group"
            )
            all_groups.append(default_group)
        all_groups.extend(other_groups)
            
        # Get the selected logic from the UI
        selected_logic = self.logic.get()
        
        # Make sure the logic is one of the allowed values
        if selected_logic.lower() not in ['any', 'all', 'n-of']:
            selected_logic = 'any'  # Default to 'any' if invalid
            
        print(f"Creating rule with main logic: {selected_logic}")
        
        # Debugging info
        print(f"Condition groups: {len(self.condition_groups)}")
        for i, group in enumerate(self.condition_groups):
            print(f"Group {i+1}: {group.name}, Logic: {group.logic}, Conditions: {len(group.conditions)}")
        
        # Save main settings
        delay_val = int(self.delay.get()) if hasattr(self, 'delay') and self.delay.get().isdigit() else 0
        popup_val = self.popup_var.get() if hasattr(self, 'popup_var') else True
    # click_type retrieval kept inline where needed; removed unused temporary variable

        # Create the rule, everything is nested in groups
        rule = Rule(
            click_position=click_position,
            condition_groups=all_groups,
            group_logic=selected_logic,
            conditions=None  # No standalone conditions at top level
        )

        # Verify rule was created correctly
        print(f"Rule created with: Group Logic = {rule.group_logic}, Click Pos = {rule.click_position}, Groups = {len(rule.condition_groups)}")

        # Create or update config
        if not hasattr(self, 'config') or not self.config:
            self.config = Config(rules=[rule], delay=delay_val, popup=popup_val)
        else:
            self.config.rules = [rule]  # Replace existing rules
            self.config.delay = delay_val
            self.config.popup = popup_val
        # Optionally store click_type in config if you want to persist it (add to Config if not present)
            
        return True
    
    def _apply_config(self, config: Config):
        # Load main settings
        if hasattr(self, 'delay') and hasattr(config, 'delay'):
            self.delay.set(str(config.delay))
        if hasattr(self, 'popup_var') and hasattr(config, 'popup'):
            self.popup_var.set(config.popup)
        if hasattr(self, 'click_type') and hasattr(config, 'click_type'):
            self.click_type.set(getattr(config, 'click_type', 'single'))
        if hasattr(self, 'logic') and config.rules and hasattr(config.rules[0], 'group_logic'):
            self.logic.set(config.rules[0].group_logic)
        """Apply a loaded configuration to the UI"""
        # Stop monitoring if active
        if self.monitor and self.monitor.is_monitoring:
            self.toggle_monitoring()
            
        # Clear current UI state
        self.conditions = []
        self.condition_groups = []
        self.selected_click_position = None
        self.selected_position = None
        self.selected_area = None
        
        # Clear UI elements
        self.conditions_listbox.delete(0, tk.END)
        for item in self.groups_listbox.get_children():
            self.groups_listbox.delete(item)
            
        # Set the config
        self.config = config
        
        # Apply the first rule (we currently support one rule per UI)
        if not config.rules:
            return
            
        rule = config.rules[0]
        
        # Set click position
        self.selected_click_position = rule.click_position
        self.click_pos_label.config(text=f"Click: ({rule.click_position[0]}, {rule.click_position[1]})")
        
        # If any group is 'Default Group', flatten all its conditions to standalone
        default_conditions = []
        other_groups = []
        for group in rule.condition_groups:
            if group.name == "Default Group":
                default_conditions.extend(group.conditions)
            else:
                other_groups.append(group)
        self.conditions = default_conditions
        self.condition_groups = other_groups
                
        # Update displays
        self.update_conditions_display()
        self.update_groups_display()
            
    # Group management methods
    def create_group(self):
        """Create a new condition group"""
        # Ask for group name and logic
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Condition Group")
        dialog.geometry("500x500")  # Increased size for better display
        dialog.minsize(500, 500)    # Set minimum size to ensure visibility
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure grid weights to ensure proper expansion
        dialog.columnconfigure(0, weight=1)
        dialog.columnconfigure(1, weight=1)
        
        # Add a help section at the top
        help_frame = ttk.LabelFrame(dialog, text="About Condition Groups")
        help_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N))
        
        help_text = """Condition groups let you organize multiple conditions with their own logic.

Logic Types:
• ALL - All conditions in the group must match (like AND)
• ANY - At least one condition must match (like OR)
• N-OF - Exactly N conditions must match (you specify N)

Example: Create a group with 3 conditions using "2-of" logic
to match when any 2 out of 3 conditions are true."""
        
        ttk.Label(help_frame, text=help_text, wraplength=380, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Form fields
        ttk.Label(dialog, text="Group Name:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=f"Group {len(self.condition_groups) + 1}")
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(dialog, text="Logic:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        # Use radio buttons for logic selection for better clarity
        logic_var = tk.StringVar(value="all")
        logic_frame = ttk.Frame(dialog)
        logic_frame.grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        # Create n_var and n_entry early so we can reference them in the radio button commands
        n_var = tk.StringVar(value="1")
        n_frame = ttk.Frame(dialog)
        n_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.W, tk.E))
        ttk.Label(n_frame, text="N value:").pack(side=tk.LEFT, padx=5)
        n_entry = ttk.Entry(n_frame, width=5, textvariable=n_var, state="disabled")
        n_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(n_frame, text="(number of conditions that must match)").pack(side=tk.LEFT, padx=5)
        
        # Create radio buttons with commands instead of using trace
        def set_all():
            n_entry.config(state="disabled")
            
        def set_any():
            n_entry.config(state="disabled")
            
        def set_n_of():
            n_entry.config(state="normal")
            
        ttk.Radiobutton(logic_frame, text="ALL (AND)", variable=logic_var, 
                       value="all", command=set_all).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(logic_frame, text="ANY (OR)", variable=logic_var, 
                       value="any", command=set_any).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(logic_frame, text="N-OF (exactly N must match)", variable=logic_var, 
                       value="n-of", command=set_n_of).pack(anchor=tk.W, pady=2)
                       
        # Create group function
        def save_group():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Group name cannot be empty")
                return
                
            logic = logic_var.get()
            n = None
            
            if logic == "n-of":
                try:
                    n = int(n_var.get())
                    if n < 1:
                        raise ValueError("N must be a positive integer")
                except ValueError:
                    messagebox.showerror("Error", "N must be a positive integer")
                    return
            
            # Create the group
            new_group = ConditionGroup(
                conditions=[],
                logic=logic,
                n=n,
                name=name
            )
            
            self.condition_groups.append(new_group)
            self.update_groups_display()
            messagebox.showinfo("Success", f"Group '{name}' created successfully!\n\nNow add conditions to this group using the 'Add to Group' button.")
            dialog.destroy()
        
        # Add buttons using direct grid placement like the Select Point/Area buttons
        ttk.Button(dialog, text="Cancel", 
                  command=dialog.destroy).grid(row=4, column=0, padx=10, pady=20)
                  
        ttk.Button(dialog, text="Create Group", 
                  command=save_group).grid(row=4, column=1, padx=10, pady=20)
        
        # Make Enter key work
        dialog.bind("<Return>", lambda event: save_group())
        name_entry.focus()
        
        def save_group():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Group name cannot be empty")
                return
                
            logic = logic_var.get()
            n = None
            
            if logic == "n-of":
                try:
                    n = int(n_var.get())
                    if n < 1:
                        raise ValueError("N must be a positive integer")
                except ValueError:
                    messagebox.showerror("Error", "N must be a positive integer")
                    return
            
            # Create the group
            new_group = ConditionGroup(
                conditions=[],
                logic=logic,
                n=n,
                name=name
            )
            
            self.condition_groups.append(new_group)
            self.update_groups_display()
            messagebox.showinfo("Success", f"Group '{name}' created successfully!\n\nNow add conditions to this group using the 'Add to Group' button.")
            dialog.destroy()
            
        # Add buttons directly to the dialog, like the Select Point/Area buttons
        ttk.Button(dialog, text="Cancel", 
                  command=dialog.destroy).grid(row=4, column=0, padx=10, pady=20)
                  
        ttk.Button(dialog, text="Create Group", 
                  command=save_group).grid(row=4, column=1, padx=10, pady=20)
        
        # Make Enter key work
        dialog.bind("<Return>", lambda event: save_group())
        name_entry.focus()
        
        # Ensure dialog appears in the correct position
        dialog.update_idletasks()
        dialog.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
            
    def edit_group(self, group_index=None):
        """Edit selected condition group or by index"""
        if group_index is None:
            selection = self.groups_listbox.selection()
            if not selection:
                messagebox.showinfo("Info", "Please select a group to edit")
                return
            group_index = int(selection[0])
        if group_index >= len(self.condition_groups):
            return
        group = self.condition_groups[group_index]
        
        # Create dialog similar to create_group but pre-filled
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Condition Group")
        dialog.geometry("500x400")  # Increased size
        dialog.minsize(500, 400)    # Set minimum size
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.columnconfigure(1, weight=1)
        
        # Add instructions at the top
        help_frame = ttk.LabelFrame(dialog, text="Edit Group Settings")
        help_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.W, tk.E))
        ttk.Label(help_frame, text="Update group settings below. Current group has " + 
                 f"{len(group.conditions)} condition(s).",
                 wraplength=400).pack(padx=10, pady=10)
        
        ttk.Label(dialog, text="Group Name:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=group.name)
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(dialog, text="Logic:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        # Use radio buttons for logic selection for better clarity
        logic_var = tk.StringVar(value=group.logic)
        logic_frame = ttk.Frame(dialog)
        logic_frame.grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        # Create n_frame and n_entry first so we can reference them in the radio button commands
        n_frame = ttk.Frame(dialog)
        n_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.W, tk.E))
        ttk.Label(n_frame, text="N value:").pack(side=tk.LEFT, padx=5)
        n_var = tk.StringVar(value=str(group.n if group.n is not None else 1))
        n_entry = ttk.Entry(n_frame, width=5, textvariable=n_var, 
                           state="normal" if group.logic == "n-of" else "disabled")
        n_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(n_frame, text="(number of conditions that must match)").pack(side=tk.LEFT, padx=5)
        
        # Define commands for radio buttons
        def set_all():
            n_entry.config(state="disabled")
            
        def set_any():
            n_entry.config(state="disabled")
            
        def set_n_of():
            n_entry.config(state="normal")
            
        # Create radio buttons with commands
        ttk.Radiobutton(logic_frame, text="ALL (AND)", variable=logic_var, 
                      value="all", command=set_all).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(logic_frame, text="ANY (OR)", variable=logic_var, 
                      value="any", command=set_any).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(logic_frame, text="N-OF (exactly N must match)", variable=logic_var, 
                      value="n-of", command=set_n_of).pack(anchor=tk.W, pady=2)
        
        def save_group():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Group name cannot be empty")
                return
                
            logic = logic_var.get()
            n = None
            
            if logic == "n-of":
                try:
                    n = int(n_var.get())
                    if n < 1:
                        raise ValueError("N must be a positive integer")
                except ValueError:
                    messagebox.showerror("Error", "N must be a positive integer")
                    return
            
            # Update the group
            group.name = name
            group.logic = logic
            group.n = n
            
            self.update_groups_display()
            messagebox.showinfo("Success", f"Group '{name}' updated successfully!")
            dialog.destroy()
            
        # Add buttons directly to dialog like the Select Point/Area buttons
        ttk.Button(dialog, text="Cancel", 
                  command=dialog.destroy).grid(row=4, column=0, padx=10, pady=20)
                  
        ttk.Button(dialog, text="Save Changes", 
                  command=save_group).grid(row=4, column=1, padx=10, pady=20)
        
        # Make Enter key work
        dialog.bind("<Return>", lambda event: save_group())
        name_entry.focus()
        
        # Ensure dialog appears in the correct position
        dialog.update_idletasks()
        dialog.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
            
    def delete_group(self, group_index=None):
        """Delete condition group by index or selection"""
        # If no index provided, get from selection
        if group_index is None:
            selection = self.groups_listbox.selection()
            if not selection:
                messagebox.showinfo("Info", "Please select a group to delete")
                return
                
            group_index = int(selection[0])
            
        # Validate index
        if group_index >= len(self.condition_groups):
            return
            
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", 
                             f"Delete group '{self.condition_groups[group_index].name}' and all its conditions?"):
            # Keep track of conditions that were only in this group
            group_conditions = self.condition_groups[group_index].conditions
            
            # Remove the group
            self.condition_groups.pop(group_index)
            
            # Move any conditions that were only in this group back to main list
            for condition in group_conditions:
                # Check if this condition is still in any other group
                in_other_group = False
                for group in self.condition_groups:
                    for group_condition in group.conditions:
                        if self._conditions_equal(condition, group_condition):
                            in_other_group = True
                            break
                    if in_other_group:
                        break
                        
                # If not in any other group and not already in standalone list, add it
                if not in_other_group and not self._condition_in_list(condition, self.conditions):
                    self.conditions.append(condition)
            
            # Update displays
            self.update_groups_display()
            
    def add_to_group(self):
        """Add selected condition to a group"""
        # Check both the unified tree and the legacy listbox for selection
        selection = self.unified_tree.selection()
        condition_selection = self.conditions_listbox.curselection()
        
        # If we have a tree selection, use that preferentially
        if selection:
            item = selection[0]
            item_type = self.unified_tree.item(item, "values")[0]
            # Only proceed if it's a standalone condition
            if item_type == "Condition" and not item.startswith("group_"):
                # Extract condition index and continue
                condition_index = int(item.split("_")[1])
                if condition_index >= len(self.conditions):
                    messagebox.showinfo("Error", "Invalid condition selection")
                    return
            else:
                messagebox.showinfo("Info", "Please select a standalone condition to add to a group")
                return
        # Fall back to legacy listbox selection
        elif condition_selection:
            condition_index = condition_selection[0]
        else:
            messagebox.showinfo("Info", "Please select a condition to add to a group")
            return
            
        if not self.condition_groups:
            if messagebox.askyesno("No Groups", "No condition groups exist. Create one now?"):
                self.create_group()
            else:
                return
                
        # Select which group to add to
        dialog = tk.Toplevel(self.root)
        dialog.title("Add to Group")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure grid
        dialog.columnconfigure(0, weight=1)
        
        # Use grid instead of pack
        ttk.Label(dialog, text="Select Group:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        group_var = tk.StringVar()
        group_combo = ttk.Combobox(dialog, textvariable=group_var, state="readonly", width=30)
        group_combo["values"] = [g.name for g in self.condition_groups]
        group_combo.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        if self.condition_groups:
            group_combo.current(0)
            
        def add_condition_to_group():
            if not group_var.get():
                messagebox.showerror("Error", "Please select a group")
                return
                
            # Find the selected group
            group_name = group_var.get()
            group = next((g for g in self.condition_groups if g.name == group_name), None)
            if not group:
                return
                
            # Add condition to the group
            # Use the condition_index we determined earlier
            if 'condition_index' not in locals():
                condition_index = condition_selection[0]
                
            if condition_index >= len(self.conditions):
                return
                
            # Check if condition already in another group
            condition = self.conditions[condition_index]
            for g in self.condition_groups:
                for i, group_condition in enumerate(g.conditions):
                    if self._conditions_equal(condition, group_condition):
                        if messagebox.askyesno("Condition In Group", 
                                             f"This condition is already in group '{g.name}'. Move it to '{group.name}'?"):
                            g.conditions.pop(i)
                        else:
                            dialog.destroy()
                            return
                        break
                        
            # Add to selected group - make a direct reference to the condition
            # to ensure we're working with the same object
            condition_to_add = self.conditions[condition_index]
            print(f"Adding condition with ID: {id(condition_to_add)}")

            # Ensure we're not already in the group (safety check)
            already_in_group = False
            for i, existing_condition in enumerate(group.conditions):
                if id(existing_condition) == id(condition_to_add) or self._conditions_equal(existing_condition, condition_to_add):
                    already_in_group = True
                    # Update the reference to use the same object
                    group.conditions[i] = condition_to_add
                    break

            if not already_in_group:
                group.conditions.append(condition_to_add)
                print(f"Added condition to group '{group.name}', now has {len(group.conditions)} conditions")

            # Remove from standalone list if present
            if condition_to_add in self.conditions:
                self.conditions.remove(condition_to_add)
                print(f"Removed condition with ID: {id(condition_to_add)} from standalone list")

            # Make sure our condition tracking is consistent
            self._ensure_conditions_consistency()

            # Update the tree view - do this first for consistency
            self.update_conditions_display()
            self.update_groups_display()

            # Expand the group in the tree view to show the newly added condition
            group_index = self.condition_groups.index(group)
            group_item_id = f"group_{group_index}"

            # Make sure the group is visible and expanded in the tree
            for item in self.unified_tree.get_children():
                if item == group_item_id:
                    self.unified_tree.item(item, text="▼")  # Set to expanded
                    self.unified_tree.see(item)  # Ensure it's visible
                    # Select the group to show it was updated
                    self.unified_tree.selection_set(item)
                    break

            messagebox.showinfo("Success", f"Condition added to group '{group.name}'")
            dialog.destroy()
            
        # Add buttons using grid like the Select Point/Area buttons - fixed column placement
        ttk.Button(dialog, text="Cancel", 
                  command=dialog.destroy).grid(row=2, column=0, padx=10, pady=20)
        
        ttk.Button(dialog, text="Add to Group", 
                  command=add_condition_to_group).grid(row=2, column=1, padx=10, pady=20)
        
    def update_groups_display(self):
        """Update the groups list (legacy compatibility) and update the unified tree view"""
        # Clear the hidden groups listbox (for backward compatibility)
        for item in self.groups_listbox.get_children():
            self.groups_listbox.delete(item)
            
        # Add each group to hidden compatibility list
        for i, group in enumerate(self.condition_groups):
            n_conditions = len(group.conditions)
            
            # Make logic text more user-friendly
            if group.logic == "all":
                logic_text = "ALL (AND)"
            elif group.logic == "any":
                logic_text = "ANY (OR)"
            elif group.logic == "n-of" and group.n is not None:
                logic_text = f"{group.n} of {n_conditions}"
            else:
                logic_text = group.logic
            
            # Create condition count text with icons
            condition_count = f"{n_conditions} condition{'s' if n_conditions != 1 else ''}"
            if n_conditions > 0:
                # Add color/text icons
                color_count = sum(1 for c in group.conditions if c.type == 'color')
                text_count = sum(1 for c in group.conditions if c.type == 'text')
                
                icons = []
                if color_count > 0:
                    icons.append(f"📊 {color_count} color")
                if text_count > 0:
                    icons.append(f"📝 {text_count} text")
                    
                condition_count = ", ".join(icons)
                
            # Add to the hidden compatibility listbox
            self.groups_listbox.insert("", tk.END, iid=str(i), values=(
                group.name,
                logic_text,
                condition_count
            ))
        
        # Now update the main unified tree
        self.update_conditions_display()
    
    def show_tree_context_menu(self, event):
        """Show context menu for tree items"""
        # Get the item under cursor
        item = self.unified_tree.identify_row(event.y)
        if not item:
            return
            
        # Select the item
        self.unified_tree.selection_set(item)
        
        # Clear the menu
        self.tree_context_menu.delete(0, tk.END)
        
        # Determine item type from tags
        tags = self.unified_tree.item(item, "tags")
        
        if "group" in tags:
            # Group item context menu
            self.tree_context_menu.add_command(label="Edit Group", 
                                              command=lambda: self.edit_selected_item())
            self.tree_context_menu.add_command(label="Delete Group", 
                                              command=lambda: self.remove_selected_item())
            self.tree_context_menu.add_separator()
            self.tree_context_menu.add_command(label="Collapse/Expand", 
                                              command=lambda: self.toggle_item_collapse(item))
        elif "condition" in tags or "group_condition" in tags:
            # Condition item context menu
            self.tree_context_menu.add_command(label="Edit Condition", 
                                              command=lambda: self.edit_selected_item())
            self.tree_context_menu.add_command(label="Remove Condition", 
                                              command=lambda: self.remove_selected_item())
            
            # If it's a standalone condition, add option to add to group
            if "condition" in tags:
                self.tree_context_menu.add_command(label="Add to Group", 
                                                 command=lambda: self.add_selected_to_group())
            # If it's a group condition, add option to remove from group
            elif "group_condition" in tags:
                self.tree_context_menu.add_command(label="Remove from Group", 
                                                 command=lambda: self.remove_from_group())
                
        # Show the menu
        self.tree_context_menu.tk_popup(event.x_root, event.y_root)
    
    def on_tree_item_double_click(self, event):
        """Handle double-click on tree items"""
        item = self.unified_tree.identify_row(event.y)
        if not item:
            return
            
        # If it's a group, toggle collapse
        if "group" in self.unified_tree.item(item, "tags"):
            self.toggle_item_collapse(item)
        # If it's a condition, edit it
        else:
            self.edit_selected_item()
    
    def toggle_item_collapse(self, item):
        """Toggle collapse/expand state of a tree item"""
        if self.unified_tree.item(item, "text") == "▼":  # Expanded
            self.unified_tree.item(item, text="▶")
            # Hide children
            for child in self.unified_tree.get_children(item):
                self.unified_tree.detach(child)
        else:  # Collapsed
            self.unified_tree.item(item, text="▼")
            # We need to re-add the children
            group_index = int(item.split("_")[1])
            if group_index < len(self.condition_groups):
                group = self.condition_groups[group_index]
                for j, condition in enumerate(group.conditions):
                    # Format condition description
                    condition_text = self._format_condition_description(condition)
                    
                    # Add as child of group
                    child_id = f"{item}_cond_{j}"
                    # Check if it exists but is detached
                    if self.unified_tree.exists(child_id):
                        self.unified_tree.move(child_id, item, 'end')
                    else:
                        self.unified_tree.insert(item, 'end', child_id, text='',
                                             values=('Condition', condition_text, ''),
                                             tags=('group_condition',))
    
    def edit_selected_item(self):
        """Edit the selected item in the tree"""
        selection = self.unified_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select an item to edit")
            return
            
        item = selection[0]
        item_type = self.unified_tree.item(item, "values")[0]
        
        if item_type == "Group":
            # Extract group index from item ID
            group_index = int(item.split("_")[1])
            self.edit_group(group_index)
        else:  # Condition
            # Find the condition based on item ID
            if item.startswith("group_"):
                # It's a condition inside a group
                parts = item.split("_")
                group_index = int(parts[1])
                condition_index = int(parts[3])
                
                # Edit this condition in the group
                if group_index < len(self.condition_groups):
                    group = self.condition_groups[group_index]
                    if condition_index < len(group.conditions):
                        condition = group.conditions[condition_index]
                        self.edit_specific_condition(condition)
            else:
                # It's a standalone condition
                condition_index = int(item.split("_")[1])
                if condition_index < len(self.conditions):
                    self.edit_specific_condition(self.conditions[condition_index])
    
    def remove_selected_item(self):
        """Remove the selected item from the tree"""
        selection = self.unified_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select an item to remove")
            return
            
        item = selection[0]
        item_type = self.unified_tree.item(item, "values")[0]
        
        if item_type == "Group":
            # Extract group index from item ID
            group_index = int(item.split("_")[1])
            self.delete_group(group_index)
        else:  # Condition
            # Find the condition based on item ID
            if item.startswith("group_"):
                # It's a condition inside a group
                parts = item.split("_")
                group_index = int(parts[1])
                condition_index = int(parts[3])
                
                # Remove this condition from the group
                if group_index < len(self.condition_groups):
                    group = self.condition_groups[group_index]
                    if condition_index < len(group.conditions):
                        # Use direct index instead of condition equality check
                        group.conditions.pop(condition_index)
                        # Update the displays
                        self.update_groups_display()
            else:
                # It's a standalone condition
                condition_index = int(item.split("_")[1])
                if condition_index < len(self.conditions):
                    del self.conditions[condition_index]
                    # Update the displays
                    self.update_conditions_display()
                    
    def add_selected_to_group(self):
        """Add selected condition to a group"""
        selection = self.unified_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a condition to add to a group")
            return
            
        item = selection[0]
        
        # Only proceed if it's a standalone condition
        if not item.startswith("group_") and self.unified_tree.item(item, "values")[0] == "Condition":
            condition_index = int(item.split("_")[1])
            if condition_index < len(self.conditions):
                # Set a selection in the hidden listbox for backward compatibility
                self.conditions_listbox.selection_clear(0, tk.END)
                self.conditions_listbox.selection_set(condition_index)
                # Use the existing add_to_group method
                self.add_to_group()
                
    def remove_from_group(self):
        """Remove a condition from its group but keep it in the standalone list"""
        selection = self.unified_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        
        # Only proceed if it's a group condition
        if item.startswith("group_") and "_cond_" in item:
            parts = item.split("_")
            group_index = int(parts[1])
            condition_index = int(parts[3])
            
            if group_index < len(self.condition_groups):
                group = self.condition_groups[group_index]
                if condition_index < len(group.conditions):
                    condition = group.conditions[condition_index]
                    # Remove from group but keep in standalone list
                    group.conditions.pop(condition_index)  # Use direct index instead of equality
                    # If not already in the standalone list, add it
                    if not self._condition_in_list(condition, self.conditions):
                        self.conditions.append(condition)
                    # Update displays
                    self.update_groups_display()
                    
    def edit_specific_condition(self, condition):
        """Edit a specific condition object"""
        # Find the condition in the main list to get its index
        found = False
        for i, main_condition in enumerate(self.conditions):
            if self._conditions_equal(condition, main_condition):
                index = i
                found = True
                break
                
        if found:
            # Set selection in hidden listbox for backward compatibility
            self.conditions_listbox.selection_clear(0, tk.END)
            self.conditions_listbox.selection_set(index)
            # Use existing edit method
            self.edit_condition()
        else:
            # It might be only in a group but not in main list
            # Add it temporarily to edit
            self.conditions.append(condition)
            index = len(self.conditions) - 1
            self.conditions_listbox.selection_clear(0, tk.END)
            self.conditions_listbox.selection_set(index)
            # Edit and remove from main list if needed
            self.edit_condition()
            # If it's only in a group, remove from main list
            in_group_only = False
            for group in self.condition_groups:
                for group_condition in group.conditions:
                    if self._conditions_equal(condition, group_condition):
                        in_group_only = True
                        break
                if in_group_only:
                    break
            if in_group_only:
                self.conditions.pop()
                
    def on_group_selected(self, event):
        """Legacy method for backward compatibility"""
        # This is kept for backward compatibility with old code
        selection = self.groups_listbox.selection()
        if not selection:
            return
            
        index = int(selection[0])
        if index >= len(self.condition_groups):
            return
        
        group = self.condition_groups[index]
        
        # Show a popup with the conditions in the group
        if not group.conditions:
            messagebox.showinfo("Group Details", 
                             f"Group: {group.name}\nLogic: {group.logic}\n\nThis group has no conditions yet. "
                             f"Add conditions to this group using the 'Add to Group' button.")
            return
            
        # Create a detailed view of the group's conditions
        details = tk.Toplevel(self.root)
        details.title(f"Group Details: {group.name}")
        details.geometry("500x400")
        details.transient(self.root)
        
        # Header with group info
        header_frame = ttk.Frame(details)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Logic explanation
        logic_explanation = ""
        if group.logic == "all":
            logic_explanation = "ALL conditions must match (AND logic)"
        elif group.logic == "any":
            logic_explanation = "ANY condition can match (OR logic)"
        elif group.logic == "n-of":
            logic_explanation = f"Exactly {group.n} of the conditions must match"
            
        ttk.Label(header_frame, text=f"Group: {group.name}", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"Logic: {logic_explanation}").pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"Conditions: {len(group.conditions)}").pack(anchor=tk.W)
        
        # List of conditions
        cond_frame = ttk.LabelFrame(details, text="Conditions in this group")
        cond_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        conditions_list = tk.Listbox(cond_frame)
        conditions_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for i, condition in enumerate(group.conditions):
            # Format similar to our improved condition display
            type_desc = "📊 Color" if condition.type == "color" else "📝 Text"
            
            value_desc = ""
            if condition.type == "color" and isinstance(condition.value, tuple) and len(condition.value) == 3:
                r, g, b = condition.value
                value_desc = f"RGB({r},{g},{b})"
            elif condition.type == "text":
                value_desc = f"\"{condition.value}\"" if len(condition.value) <= 20 else f"\"{condition.value[:17]}...\""
            
            # Position description
            if len(condition.position) == 4:
                x1, y1, x2, y2 = condition.position
                position_desc = f"Area: ({x1},{y1}) to ({x2},{y2})"
            else:
                x, y = condition.position
                position_desc = f"Point({x},{y})"
                
            # Build full description
            desc = f"{i+1}. {type_desc}: {value_desc} at {position_desc}"
            conditions_list.insert(tk.END, desc)
        
        ttk.Button(details, text="Close", command=details.destroy).pack(pady=10)

if __name__ == "__main__":
    app = AutoclickerUI()
    app.run()
