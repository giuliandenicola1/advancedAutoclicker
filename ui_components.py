import tkinter as tk
from tkinter import ttk


class UIComponentsMixin:
    """
    Mixin class for UI setup and layout components.
    Contains methods for creating and managing the UI layout.
    """
    
    def center_window(self, window, width, height):
        """Center a window on the screen"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    def optimize_window_size(self):
        """Optimize window size based on current content."""
        if hasattr(self, 'root'):
            self.root.update_idletasks()
            
            # Calculate optimal size based on notebook content
            if hasattr(self, 'notebook'):
                req_width = self.notebook.winfo_reqwidth() + 30  # Reduced padding
                req_height = self.notebook.winfo_reqheight() + 60  # Reduced padding
                
                # Ensure reasonable bounds
                width = max(min(req_width, 1200), 800)
                height = max(min(req_height, 750), 600)  # Reduced max height
                
                current_geo = self.root.geometry()
                if 'x' in current_geo and '+' in current_geo:
                    # Preserve position, update size only
                    parts = current_geo.split('+')
                    if len(parts) >= 3:
                        x_pos = parts[1]
                        y_pos = parts[2]
                        self.root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
                    else:
                        self.center_window(self.root, width, height)
                else:
                    self.center_window(self.root, width, height)
    
    def setup_ui(self):
        """Set up the modern responsive tabbed UI interface."""
        # Create main notebook for tabs with no padding
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create all tabs
        self.setup_main_tab()
        self.setup_monitoring_tab()
        
        # Set up menu bar
        self.setup_menu_bar()
        
    def setup_menu_bar(self):
        """Create the menu bar."""
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
        if hasattr(self, 'style') and self.style is not None:
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
                    self.logger.log_info(f"Applied theme: {theme_name}", "ui")
                except Exception as e:
                    self.logger.log_error(f"Failed to apply theme {theme_name}: {e}", "ui")

            for label, name in themes:
                theme_menu.add_command(label=label, command=lambda n=name: _apply_theme(n))
                
    def setup_main_tab(self):
        """Set up the main configuration tab with optimized scrollable layout."""
        # Create main tab frame with minimal padding
        self.main_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab_frame, text="Configuration")
        
        # Create canvas and scrollbar for scrolling with minimal spacing
        # Use theme background so empty areas match the app instead of white
        self.canvas = tk.Canvas(self.main_tab_frame, highlightthickness=0, bd=0)
        try:
            bg = None
            if hasattr(self, 'style') and self.style is not None:
                bg = self.style.lookup('TFrame', 'background') or self.style.lookup('Frame', 'background')
            if not bg:
                bg = self.root.cget('background')
            self.canvas.configure(bg=bg)
        except Exception:
            # Fallback if style lookup fails
            self.canvas.configure(bg=self.root.cget('bg'))
        self.scrollbar = ttk.Scrollbar(self.main_tab_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Keep a reference to the window so we can control its width on resize
        self._scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        # Make the inner frame stretch to the canvas width to avoid right gutter
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Grid the canvas and scrollbar with no padding
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        self.main_tab_frame.grid_columnconfigure(0, weight=1)
        self.main_tab_frame.grid_rowconfigure(0, weight=1)
        
        # Set main_frame to the scrollable frame with minimal padding
        self.main_frame = ttk.Frame(self.scrollable_frame, padding=(6, 4))  # Reduced from (8, 8)
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure responsive grid weights for full width utilization
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)  # Single column that expands
        
        # Configure row weights for compact spacing
        for r in range(12):
            self.main_frame.grid_rowconfigure(r, weight=0)
        
        # Create sections with full width and reduced spacing
        self.create_toolbar()
        self.create_position_section()
        self.create_conditions_section()
        self.create_settings_section()  # This will now include click position and logic
        self.create_control_buttons()
        self.create_status_section()
        
        # Bind mousewheel to canvas
        self._bind_mousewheel()

    def _on_canvas_configure(self, event):
        """Keep the scrollable frame width equal to the visible canvas width."""
        try:
            if hasattr(self, '_scrollable_window'):
                # Match inner window width to canvas width so content expands horizontally
                self.canvas.itemconfigure(self._scrollable_window, width=event.width)
            # Always keep scrollregion updated
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass
        
    def _bind_mousewheel(self):
        """Bind mousewheel events to canvas for scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
        
    def create_toolbar(self):
        """Create responsive toolbar with common actions."""
        toolbar = ttk.Frame(self.main_frame, padding=(4, 2))  # Reduced padding
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 3))  # Reduced pady
        # Let the name entry expand
        for c in range(6):
            toolbar.grid_columnconfigure(c, weight=0)
        toolbar.grid_columnconfigure(5, weight=1)
        
        # Center the buttons
        ttk.Button(toolbar, text="New", command=self.new_config).grid(row=0, column=0, padx=2, pady=1)
        ttk.Button(toolbar, text="Open", command=self.load_config).grid(row=0, column=1, padx=2, pady=1)
        ttk.Button(toolbar, text="Save", command=self.save_config).grid(row=0, column=2, padx=2, pady=1)

        # Configuration name inline with buttons
        ttk.Label(toolbar, text="Name:").grid(row=0, column=3, padx=(12, 4), pady=1, sticky=tk.E)
        name_entry = ttk.Entry(toolbar, textvariable=self.config_name_var, font=('Segoe UI', 10))
        name_entry.grid(row=0, column=4, padx=(0, 4), pady=1, sticky=(tk.W, tk.E))
        # Spacer to push entry to take remaining width
        ttk.Frame(toolbar).grid(row=0, column=5, sticky=(tk.W, tk.E))
        
    def create_config_name_section(self):
        """Deprecated: configuration name is now inline in the toolbar."""
        pass
        
    def create_position_section(self):
        """Create responsive position selection section."""
        pos_frame = ttk.LabelFrame(self.main_frame, text="Detection Area", padding=(4, 2))  # Reduced padding
        pos_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=1)  # Reduced pady
        pos_frame.columnconfigure(2, weight=1)  # Make label column expandable

        ttk.Button(pos_frame, text="Select Point", command=self.select_position).grid(
            row=0, column=0, padx=2, pady=1  # Reduced padx/pady
        )
        ttk.Button(pos_frame, text="Select Area", command=self.select_area).grid(
            row=0, column=1, padx=2, pady=1  # Reduced padx/pady
        )

        self.pos_label = ttk.Label(pos_frame, text="No position/area selected", 
                                  font=('Segoe UI', 9), foreground='gray')
        self.pos_label.grid(row=0, column=2, padx=(8, 2), pady=1, sticky=(tk.W, tk.E))  # Reduced padx/pady
        
    def create_conditions_section(self):
        """Create responsive conditions management section."""
        cond_frame = ttk.LabelFrame(self.main_frame, text="Conditions", padding=(4, 2))  # Reduced padding
        cond_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=1)  # Reduced pady
        cond_frame.columnconfigure(1, weight=1)  # Make value column expandable

        # Condition type selection
        ttk.Label(cond_frame, text="Type:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)  # Reduced pady
        type_frame = ttk.Frame(cond_frame)
        type_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)  # Reduced pady
        self.condition_type = tk.StringVar(value='color')
        ttk.Radiobutton(type_frame, text="Color", variable=self.condition_type, 
                       value='color', command=self.on_type_change).pack(side=tk.LEFT, padx=6)  # Reduced padx
        ttk.Radiobutton(type_frame, text="Text", variable=self.condition_type, 
                       value='text', command=self.on_type_change).pack(side=tk.LEFT, padx=6)  # Reduced padx

        # Value selection
        ttk.Label(cond_frame, text="Value:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)  # Reduced pady
        self.value_frame = ttk.Frame(cond_frame)
        self.value_frame.grid(row=1, column=1, padx=2, sticky=(tk.W, tk.E), pady=2)  # Reduced padx/pady

    # Create value widgets (will be shown/hidden based on type)
        self.color_button = ttk.Button(self.value_frame, text="Pick Color", command=self.pick_color)
        self.color_label = ttk.Label(self.value_frame, text="No color selected", foreground='gray')
        self.text_entry = ttk.Entry(self.value_frame, width=40, font=('Segoe UI', 10))

        # Comparator selection
        ttk.Label(cond_frame, text="Comparator:", font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)  # Reduced pady
        self.comparator = ttk.Combobox(cond_frame, values=['equals', 'contains', 'similar'], 
                                     state='readonly', width=15, font=('Segoe UI', 10))
        self.comparator.grid(row=2, column=1, padx=2, sticky=tk.W, pady=2)  # Reduced padx/pady
        self.comparator.set('equals')

        # Tolerance setting
        ttk.Label(cond_frame, text="Tolerance:", font=('Segoe UI', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=2)  # Reduced pady
        tolerance_frame = ttk.Frame(cond_frame)
        tolerance_frame.grid(row=3, column=1, padx=2, sticky=(tk.W, tk.E), pady=2)  # Reduced padx/pady
        tolerance_frame.columnconfigure(0, weight=1)
        
        self.tolerance = ttk.Scale(tolerance_frame, from_=0, to=50, orient=tk.HORIZONTAL)
        self.tolerance.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))  # Reduced padx
        self.tolerance.set(10)
        
        self.tolerance_label = ttk.Label(tolerance_frame, text="10", width=5)
        self.tolerance_label.grid(row=0, column=1, sticky=tk.E)
        
        # Update tolerance label when changed
        def update_tolerance_label(value):
            self.tolerance_label.config(text=f"{int(float(value))}")
        self.tolerance.config(command=update_tolerance_label)

        # Action buttons - positioned under the condition fields
        action_buttons = ttk.Frame(cond_frame)
        action_buttons.grid(row=4, column=0, columnspan=2, pady=4)  # Reduced pady
        
        ttk.Button(action_buttons, text="Add Condition", 
                  command=self.add_condition).pack(side=tk.LEFT, padx=2)  # Reduced padx
        ttk.Button(action_buttons, text="New Group", 
                  command=self.create_group).pack(side=tk.LEFT, padx=2)  # Reduced padx
        ttk.Button(action_buttons, text="Edit Selected", 
                  command=self.edit_selected_item).pack(side=tk.LEFT, padx=2)  # Reduced padx
        ttk.Button(action_buttons, text="Remove Selected", 
                  command=self.remove_selected_item).pack(side=tk.LEFT, padx=2)  # Reduced padx

        # Conditions display
        self.create_conditions_display(cond_frame)
        
        # Initialize the value widgets display
        self.on_type_change()
        
    def create_conditions_display(self, parent):
        """Create responsive conditions + groups display (unified tree)."""
        conditions_frame = ttk.LabelFrame(parent, text="Conditions and Groups", padding=(4, 2))  # Reduced padding
        conditions_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=3)
        conditions_frame.columnconfigure(0, weight=1)
        conditions_frame.rowconfigure(0, weight=1)

        # Container
        tree_container = ttk.Frame(conditions_frame)
        tree_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        # Treeview
        self.unified_tree = ttk.Treeview(
            tree_container,
            columns=("type", "details", "logic"),
            show="tree headings",
            height=5,
        )
        self.unified_tree.heading("#0", text="", anchor="w")
        self.unified_tree.heading("type", text="Type", anchor="w")
        self.unified_tree.heading("details", text="Details", anchor="w")
        self.unified_tree.heading("logic", text="Logic", anchor="w")
        self.unified_tree.column("#0", width=40, minwidth=30)
        self.unified_tree.column("type", width=120, minwidth=80)
        self.unified_tree.column("details", width=350, minwidth=200)
        self.unified_tree.column("logic", width=100, minwidth=60)

        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.unified_tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.unified_tree.xview)
        self.unified_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.unified_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scroll.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Context menu + bindings
        self.tree_context_menu = tk.Menu(self.unified_tree, tearoff=0)
        self.unified_tree.bind("<Button-3>", self.show_tree_context_menu)
        self.unified_tree.bind("<Button-2>", self.show_tree_context_menu)  # some macOS builds
        self.unified_tree.bind("<Control-Button-1>", self.show_tree_context_menu)  # macOS ctrl-click
        self.unified_tree.bind("<Double-1>", self.on_tree_item_double_click)

        # Hidden legacy widgets (compatibility with other mixins)
        self.conditions_listbox = tk.Listbox()
        self.groups_listbox = ttk.Treeview(columns=("name", "logic", "conditions"))
        
    def create_settings_section(self):
        """Create expanded settings section with click position and logic."""
        settings_frame = ttk.LabelFrame(self.main_frame, text="Settings", padding=(4, 3))  # Reduced padding
        settings_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=2)  # Reduced pady
        settings_frame.columnconfigure(1, weight=1)
        
        # Required Click Position
        ttk.Label(settings_frame, text="Click Position (required):", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        click_container = ttk.Frame(settings_frame)
        click_container.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=3, pady=3)
        click_container.columnconfigure(1, weight=1)
        
        ttk.Button(click_container, text="Set Click Position", command=self.select_click_position).grid(
            row=0, column=0, sticky=tk.W)
        self.click_pos_label = ttk.Label(click_container, text="Click: Not set", 
                                         font=('Segoe UI', 9, 'italic'), foreground='orange')
        self.click_pos_label.grid(row=0, column=1, padx=(8, 0), sticky=(tk.W, tk.E))
        
        # Rule Logic
        ttk.Label(settings_frame, text="Rule Logic:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)  # Reduced pady
        logic_container = ttk.Frame(settings_frame)
        logic_container.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=3, pady=3)  # Reduced padx/pady
        
        self.logic = ttk.Combobox(logic_container, values=['any', 'all', 'n-of'], 
                                state='readonly', width=12, font=('Segoe UI', 10))
        self.logic.grid(row=0, column=0, sticky=tk.W)
        self.logic.set('any')
        self.logic.bind('<<ComboboxSelected>>', self.on_logic_change)
        
        self.n_label = ttk.Label(logic_container, text="N:", font=('Segoe UI', 10))
        self.n_label.grid(row=0, column=1, padx=(8, 4), sticky=tk.W)  # Reduced padx
        self.n_entry = ttk.Entry(logic_container, width=6, font=('Segoe UI', 10))
        self.n_entry.grid(row=0, column=2, sticky=tk.W)
        
        # Delay setting
        ttk.Label(settings_frame, text="Delay (seconds):", font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=3)  # Reduced pady
        delay_container = ttk.Frame(settings_frame)
        delay_container.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=3, pady=3)  # Reduced padx/pady
        
        self.delay = ttk.Combobox(delay_container, values=['0', '3', '5', '10', '15', '30'], 
                                width=10, font=('Segoe UI', 10))
        self.delay.grid(row=0, column=0, sticky=tk.W)
        self.delay.set('0')
        self.delay.bind('<<ComboboxSelected>>', self._on_delay_change)
        self.delay.bind('<KeyRelease>', self._on_delay_change)
        self.delay.bind('<FocusOut>', self._on_delay_change)
        
        # Popup checkbox (will be controlled by delay setting)
        self.popup_var = tk.BooleanVar(value=True)
        self.popup_checkbox = ttk.Checkbutton(settings_frame, text="Show confirmation popup", 
                                            variable=self.popup_var, style='TCheckbutton')
        self.popup_checkbox.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=4)  # Reduced pady
        
        # Initialize popup state
        self._on_delay_change()
        
        # Click type setting
        ttk.Label(settings_frame, text="Click type:", font=('Segoe UI', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=3)  # Reduced pady
        click_type_container = ttk.Frame(settings_frame)
        click_type_container.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=3, pady=3)  # Reduced padx/pady
        
        self.click_type = ttk.Combobox(click_type_container, values=['single', 'double', 'right'], 
                                     width=10, state='readonly', font=('Segoe UI', 10))
        self.click_type.grid(row=0, column=0, sticky=tk.W)
        self.click_type.set('single')
        
    def create_control_buttons(self):
        """Create responsive control buttons section."""
        control_frame = ttk.Frame(self.main_frame, padding=(4, 3))  # Reduced padding
        control_frame.grid(row=5, column=0, pady=3)  # Reduced pady
        control_frame.grid_columnconfigure(1, weight=1)  # Center the buttons
        
        # Create button container for centering
        button_container = ttk.Frame(control_frame)
        button_container.grid(row=0, column=1)
        
        self.start_button = ttk.Button(button_container, text="Start Monitoring", 
                                     command=self.start_monitoring, width=16)
        self.start_button.grid(row=0, column=0, padx=3)  # Reduced padx
        
        self.stop_button = ttk.Button(button_container, text="Stop Monitoring", 
                                    command=self.stop_monitoring, state='disabled', width=16)
        self.stop_button.grid(row=0, column=1, padx=3)  # Reduced padx
        
        self.logs_button = ttk.Button(button_container, text="View Logs", 
                                    command=self.show_logs_window, width=16)
        self.logs_button.grid(row=0, column=2, padx=3)  # Reduced padx
        
    def create_status_section(self):
        """Create responsive status display section."""
        status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding=(4, 3))  # Reduced padding
        status_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=2)  # Reduced pady
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready", 
                                     font=('Segoe UI', 10, 'bold'), foreground='green')
        self.status_label.grid(row=0, column=0, pady=3)  # Reduced pady
        
    def setup_monitoring_tab(self):
        """Set up the monitoring and logs tab."""
        # Call the monitoring mixin setup
        from ui_monitoring import UIMonitoringMixin
        if hasattr(self, 'setup_monitoring_tab') and isinstance(self, UIMonitoringMixin):
            super().setup_monitoring_tab()
        else:
            # Fallback if mixin isn't properly initialized
            self.create_basic_monitoring_tab()
            
    def create_basic_monitoring_tab(self):
        """Create a basic monitoring tab if mixin isn't available."""
        # Create monitoring tab frame with reduced padding
        self.monitoring_frame = ttk.Frame(self.notebook, padding=(8, 8))
        self.notebook.add(self.monitoring_frame, text="Monitoring & Logs")
        
        # Configure grid weights
        self.monitoring_frame.grid_columnconfigure(0, weight=1)
        self.monitoring_frame.grid_rowconfigure(1, weight=1)
        
        # Create basic status widgets that the monitoring mixin expects
        monitor_frame = ttk.LabelFrame(self.monitoring_frame, text="Real-time Monitor", padding=(8, 6))
        monitor_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        monitor_frame.columnconfigure(1, weight=1)
        
        # Status display
        ttk.Label(monitor_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.monitor_status_label = ttk.Label(monitor_frame, text="⏹️ Not monitoring", foreground="orange")
        self.monitor_status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Click count
        ttk.Label(monitor_frame, text="Clicks performed:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.click_count_label = ttk.Label(monitor_frame, text="0")
        self.click_count_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Last action
        ttk.Label(monitor_frame, text="Last action:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.last_action_label = ttk.Label(monitor_frame, text="None")
        self.last_action_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))

    def lock_configuration(self, lock: bool):
        """Show a locked view with a Stop button when monitoring is active."""
        if not hasattr(self, 'main_tab_frame'):
            return
        # Create locked frame lazily
        if lock and not hasattr(self, 'config_locked_frame'):
            self.config_locked_frame = ttk.Frame(self.main_tab_frame, padding=(12, 12))
            self.config_locked_frame.grid_columnconfigure(0, weight=1)
            msg = ttk.Label(self.config_locked_frame,
                            text="Monitoring is active. Configuration is locked.",
                            font=('Segoe UI', 12, 'bold'))
            msg.grid(row=0, column=0, pady=(0, 10))
            stop_btn = ttk.Button(self.config_locked_frame, text="Stop Monitoring",
                                  command=self.stop_monitoring, width=18)
            stop_btn.grid(row=1, column=0)
        try:
            if lock:
                # Hide scrollable config (canvas + scrollbar)
                self.canvas.grid_remove()
                self.scrollbar.grid_remove()
                # Show locked view
                self.config_locked_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.N, tk.S, tk.W, tk.E))
                # Optionally mark tab title as locked
                try:
                    idx = self.notebook.index(self.main_tab_frame)
                    self.notebook.tab(idx, text="Configuration (Locked)")
                except Exception:
                    pass
            else:
                # Hide locked view
                if hasattr(self, 'config_locked_frame'):
                    self.config_locked_frame.grid_remove()
                # Show scrollable config
                self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
                # Restore tab title
                try:
                    idx = self.notebook.index(self.main_tab_frame)
                    self.notebook.tab(idx, text="Configuration")
                except Exception:
                    pass
                # Ensure scroll region is correct
                self.update_canvas_scroll_region()
        except Exception:
            pass
        
    def reset_ui_state(self):
        """Reset all UI elements to their default state."""
        # Reset labels
        if hasattr(self, 'pos_label'):
            self.pos_label.config(text="No position/area selected")
        if hasattr(self, 'click_pos_label'):
            self.click_pos_label.config(text="Click: Not set")
            
        # Clear tree view
        if hasattr(self, 'unified_tree'):
            for item in self.unified_tree.get_children():
                self.unified_tree.delete(item)
                
        # Clear hidden compatibility widgets
        if hasattr(self, 'conditions_listbox'):
            self.conditions_listbox.delete(0, tk.END)
        if hasattr(self, 'groups_listbox'):
            for item in self.groups_listbox.get_children():
                self.groups_listbox.delete(item)
        
        # Reset condition editor widgets
        try:
            if hasattr(self, 'condition_type'):
                self.condition_type.set('color')
            if hasattr(self, 'comparator'):
                self.comparator.set('equals')
            if hasattr(self, 'tolerance'):
                self.tolerance.set(10)
            if hasattr(self, 'tolerance_label'):
                self.tolerance_label.config(text="10")
            if hasattr(self, 'text_entry'):
                self.text_entry.delete(0, tk.END)
            if hasattr(self, 'color_label'):
                self.color_label.config(text="No color selected", foreground='gray')
            if hasattr(self, 'logic'):
                self.logic.set('any')
                if hasattr(self, 'on_logic_change'):
                    self.on_logic_change()
            if hasattr(self, 'n_entry'):
                self.n_entry.delete(0, tk.END)
            if hasattr(self, 'delay'):
                self.delay.set('0')
                if hasattr(self, '_on_delay_change'):
                    self._on_delay_change()
            if hasattr(self, 'popup_var'):
                self.popup_var.set(True)
            if hasattr(self, 'click_type'):
                self.click_type.set('single')
            if hasattr(self, 'on_type_change'):
                self.on_type_change()
        except Exception:
            pass

        # Reset status label
        if hasattr(self, 'status_label'):
            self.status_label.grid(row=0, column=0, pady=3)  # Reduced pady
        
    def update_canvas_scroll_region(self):
        """Update the canvas scroll region after content changes."""
        if hasattr(self, 'canvas') and hasattr(self, 'scrollable_frame'):
            self.root.after_idle(lambda: [
                self.canvas.update_idletasks(),
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            ])
            
    def _on_delay_change(self, event=None):
        """Handle delay field changes to update popup checkbox state."""
        try:
            # Validate numeric input (side-effect only); keep popup enabled regardless of delay
            _ = int(self.delay.get()) if self.delay.get().isdigit() else 0
            # Always keep popup enabled; zero delay just means immediate confirmation possible
            self.popup_checkbox.configure(state='normal')
        except ValueError:
            # Handle invalid input gracefully
            pass
