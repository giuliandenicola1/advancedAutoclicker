from tkinter import messagebox, filedialog
import json
import datetime
from config import Config, Rule, ConditionGroup
try:
    from version import __version__ as APP_VERSION
except Exception:
    APP_VERSION = "0.0.0"


class UIConfigMixin:
    """
    Mixin class for configuration save/load functionality.
    Contains methods for saving and loading configuration files.
    """
    
    def save_config(self):
        """Save the current configuration to a file"""
        # Create a rule from the current UI state
        if not self._create_rule_from_ui():
            messagebox.showerror("Save Error", "Unable to create a valid configuration from current settings.")
            return
            
        # Get file path with default name autoclicker_[date]_[time].json
        now = datetime.datetime.now()
        today_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        
        # Use config name if provided, else default
        config_name = self.config_name_var.get().strip()
        if config_name:
            # Sanitize filename and replace spaces with underscores
            safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')  # Replace spaces with underscores
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
            # Save the configuration
            config_dict = self.config.to_dict()
            
            # Add metadata
            config_dict["metadata"] = {
                "name": config_name if config_name else "Unnamed Configuration",
                "created": now.isoformat(),
                "version": APP_VERSION,
                "total_conditions": len(self.conditions) + sum(len(g.conditions) for g in self.condition_groups),
                "total_groups": len(self.condition_groups)
            }
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            messagebox.showinfo("Save Successful", f"Configuration saved to:\n{file_path}")
            
            self.logger.log_action("SAVE_CONFIG", {
                "file_path": file_path,
                "config_name": config_name,
                "conditions_count": len(self.conditions),
                "groups_count": len(self.condition_groups)
            }, success=True)
            
        except Exception as e:
            self.logger.log_error(f"Failed to save config: {e}", "ui")
            messagebox.showerror("Save Error", f"Failed to save configuration:\n{str(e)}")
    
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
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
                
            # Create config object from dictionary
            config = Config.from_dict(config_dict)
            
            # Apply the loaded configuration
            self._apply_config(config)
            
            # Extract filename for configuration name
            import os
            filename = os.path.basename(file_path)
            # Remove .json extension if present
            if filename.lower().endswith('.json'):
                filename = filename[:-5]
            # Replace underscores with spaces for display
            display_name = filename.replace('_', ' ')
            
            # Set config name - prefer filename over metadata
            if "metadata" in config_dict and "name" in config_dict["metadata"]:
                config_name = config_dict["metadata"]["name"]
                if config_name != "Unnamed Configuration":
                    # Use metadata name if it exists and is not default
                    self.config_name_var.set(config_name)
                else:
                    # Use filename-based name if metadata name is default
                    self.config_name_var.set(display_name)
            else:
                # Use filename-based name if no metadata
                self.config_name_var.set(display_name)
                    
            messagebox.showinfo("Load Successful", f"Configuration loaded from:\n{file_path}")
            
            self.logger.log_action("LOAD_CONFIG", {
                "file_path": file_path,
                "conditions_count": len(self.conditions),
                "groups_count": len(self.condition_groups)
            }, success=True)
            
        except Exception as e:
            self.logger.log_error(f"Failed to load config: {e}", "ui")
            messagebox.showerror("Load Error", f"Failed to load configuration:\n{str(e)}")
    
    def _create_rule_from_ui(self):
        """Create a rule from the current UI state"""
        # Check for required fields
        if not self.condition_groups and not self.conditions:
            messagebox.showerror("Configuration Error", "Please add at least one condition or group.")
            return False
            
        # Get the click position (mandatory)
        click_position = self.selected_click_position
        if not click_position:
            messagebox.showerror("Configuration Error", "Click Position is required. Please set it in Settings.")
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
                name="Default Group",
                logic=self.logic.get() if hasattr(self, 'logic') else 'any',
                n=None,
                conditions=merged_default_conditions
            )
            all_groups.append(default_group)
        all_groups.extend(other_groups)
            
        # Get the selected logic from the UI
        selected_logic = self.logic.get() if hasattr(self, 'logic') else 'any'
        
        # Make sure the logic is one of the allowed values
        if selected_logic.lower() not in ['any', 'all', 'n-of']:
            selected_logic = 'any'
            
        print(f"Creating rule with main logic: {selected_logic}")
        
        # Debugging info
        print(f"Condition groups: {len(self.condition_groups)}")
        for i, group in enumerate(self.condition_groups):
            print(f"  Group {i}: {group.name} with {len(group.conditions)} conditions")
        
        # Save main settings
        delay_val = int(self.delay.get()) if hasattr(self, 'delay') and self.delay.get().isdigit() else 0
        popup_val = self.popup_var.get() if hasattr(self, 'popup_var') else True
        # click_type_val = self.click_type.get() if hasattr(self, 'click_type') else 'single'  # Future use

        # Create the rule, everything is nested in groups
        rule = Rule(
            click_position=click_position,
            condition_groups=all_groups,
            group_logic=selected_logic,
            conditions=None  # All conditions are now in groups
        )

        # Verify rule was created correctly
        print(f"Rule created with: Group Logic = {rule.group_logic}, Click Pos = {rule.click_position}, Groups = {len(rule.condition_groups)}")

        # Create or update config
        if not hasattr(self, 'config') or not self.config:
            self.config = Config(rules=[rule], delay=delay_val, popup=popup_val)
        else:
            self.config.rules = [rule]
            self.config.delay = delay_val
            self.config.popup = popup_val
            
        # Optionally store click_type in config if you want to persist it (add to Config if not present)
            
        return True
    
    def _apply_config(self, config: Config):
        """Apply a loaded configuration to the UI"""
        # Stop monitoring if active
        if hasattr(self, 'monitor') and self.monitor and getattr(self.monitor, 'is_monitoring', False):
            self.stop_monitoring()
            
        # Clear current UI state
        self.conditions = []
        self.condition_groups = []
        self.selected_click_position = None
        self.selected_position = None
        self.selected_area = None
        
        # Clear UI elements
        self.reset_ui_state()
            
        # Set the config
        self.config = config
        
        # Load main settings
        if hasattr(self, 'delay') and hasattr(config, 'delay'):
            self.delay.set(str(config.delay) if config.delay is not None else '0')
        if hasattr(self, 'popup_var') and hasattr(config, 'popup'):
            self.popup_var.set(config.popup if config.popup is not None else True)
        if hasattr(self, 'click_type') and hasattr(config, 'click_type'):
            self.click_type.set(config.click_type if config.click_type else 'single')
        if hasattr(self, 'logic') and config.rules and hasattr(config.rules[0], 'group_logic'):
            self.logic.set(config.rules[0].group_logic if config.rules[0].group_logic else 'any')
        
        # Apply the first rule (we currently support one rule per UI)
        if not config.rules:
            messagebox.showwarning("Empty Configuration", "The loaded configuration contains no rules.")
            return
            
        rule = config.rules[0]
        
        # Convert any RGBA colors to RGB for compatibility
        self._convert_colors_to_rgb(rule)
        
        # Set click position
        self.selected_click_position = rule.click_position
        if hasattr(self, 'click_pos_label'):
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
        
        # Update delay-related UI state
        self._on_delay_change()
        
        # If we have a position from the first condition, set it as selected
        if self.conditions:
            first_condition = self.conditions[0]
            if len(first_condition.position) == 4:
                self.selected_area = first_condition.position
                self.selected_position = None
                x1, y1, x2, y2 = first_condition.position
                width = x2 - x1
                height = y2 - y1
                position_text = f"Area: ({x1}, {y1}) to ({x2}, {y2}) [{width}x{height}]"
            else:
                self.selected_position = first_condition.position
                self.selected_area = None
                position_text = f"Position: {first_condition.position}"
                
            if hasattr(self, 'pos_label'):
                self.pos_label.config(text=position_text)
        elif self.condition_groups and self.condition_groups[0].conditions:
            first_condition = self.condition_groups[0].conditions[0]
            if len(first_condition.position) == 4:
                self.selected_area = first_condition.position
                self.selected_position = None
                x1, y1, x2, y2 = first_condition.position
                width = x2 - x1
                height = y2 - y1
                position_text = f"Area: ({x1}, {y1}) to ({x2}, {y2}) [{width}x{height}]"
            else:
                self.selected_position = first_condition.position
                self.selected_area = None
                position_text = f"Position: {first_condition.position}"
                
            if hasattr(self, 'pos_label'):
                self.pos_label.config(text=position_text)

    def _convert_colors_to_rgb(self, rule):
        """Convert any RGBA color values to RGB for compatibility"""
        # Convert colors in condition groups
        for group in rule.condition_groups:
            for condition in group.conditions:
                if condition.type == "color" and isinstance(condition.value, (list, tuple)) and len(condition.value) == 4:
                    # Convert RGBA to RGB
                    condition.value = condition.value[:3]
        
        # Convert colors in standalone conditions (if any)
        if hasattr(rule, "conditions") and rule.conditions:
            for condition in rule.conditions:
                if condition.type == "color" and isinstance(condition.value, (list, tuple)) and len(condition.value) == 4:
                    # Convert RGBA to RGB
                    condition.value = condition.value[:3]
