import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
from config import Condition


class UIConditionsMixin:
    """
    Mixin class for condition management functionality.
    Contains methods for creating, editing, and managing conditions.
    """
    
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
                "color": pixel_color[:3]
            }, success=True)
            
        except Exception as e:
            self.logger.log_error(f"Failed to select position: {e}", "ui")
            messagebox.showerror("Error", f"Failed to select position: {e}")
        
        finally:
            self.root.deiconify()
    
    def select_area(self):
        """Let user select an area on screen by clicking two points"""
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Area Selection", 
                              "First, click OK then click the TOP-LEFT corner of the area.")
            
            # Get first point
            point1 = pyautogui.position()
            
            messagebox.showinfo("Area Selection", 
                              "Now click the BOTTOM-RIGHT corner of the area.")
            
            # Get second point
            point2 = pyautogui.position()
            
            # Create area tuple (x1, y1, x2, y2)
            x1, y1 = min(point1[0], point2[0]), min(point1[1], point2[1])
            x2, y2 = max(point1[0], point2[0]), max(point1[1], point2[1])
            self.selected_area = (x1, y1, x2, y2)
            self.selected_position = None  # Clear point selection when selecting area
            
            width = x2 - x1
            height = y2 - y1
            self.pos_label.config(text=f"Area: ({x1}, {y1}) to ({x2}, {y2}) [{width}x{height}]")
            
            self.logger.log_action("SELECT_AREA", {
                "area": self.selected_area,
                "size": f"{width}x{height}"
            }, success=True)
            
        except Exception as e:
            self.logger.log_error(f"Failed to select area: {e}", "ui")
            messagebox.showerror("Error", f"Failed to select area: {e}")
        
        finally:
            self.root.deiconify()
    
    def select_click_position(self):
        """Let user select a separate click position"""
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Click Position Selection", 
                              "Move your mouse to where you want clicks to occur and click OK.")
            
            self.selected_click_position = pyautogui.position()
            self.click_pos_label.config(text=f"Click: ({self.selected_click_position[0]}, {self.selected_click_position[1]})")
            
            self.logger.log_action("SELECT_CLICK_POSITION", {
                "position": self.selected_click_position
            }, success=True)
            
        except Exception as e:
            self.logger.log_error(f"Failed to select click position: {e}", "ui")
            messagebox.showerror("Error", f"Failed to select click position: {e}")
        
        finally:
            self.root.deiconify()
        
    def on_type_change(self, event=None):
        """Handle condition type change"""
        # Clear previous widgets
        for widget in self.value_frame.winfo_children():
            widget.pack_forget()
            
        current_type = self.condition_type.get()
        if current_type == 'color':
            self.color_button.pack(side=tk.LEFT, padx=5)
            self.color_label.pack(side=tk.LEFT, padx=10)
        else:  # text
            self.text_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
    def pick_color(self):
        """Capture color from screen at current mouse position"""
        # Hide the main window temporarily
        self.root.withdraw()
        
        try:
            messagebox.showinfo("Color Picker", 
                              "Move your mouse over the target color and click OK to capture it.")
            
            # Get mouse position and capture color
            pos = pyautogui.position()
            screenshot = pyautogui.screenshot()
            pixel_color = screenshot.getpixel(pos)
            
            # Ensure we only store RGB (first 3 values) to avoid RGBA issues
            self.selected_color = pixel_color[:3] if len(pixel_color) > 3 else pixel_color
            
            # Update UI to show selected color
            color_text = f"RGB({self.selected_color[0]}, {self.selected_color[1]}, {self.selected_color[2]})"
            self.color_label.config(text=color_text)
            
            self.logger.log_action("PICK_COLOR", {
                "position": pos,
                "color": self.selected_color
            }, success=True)
            
        except Exception as e:
            self.logger.log_error(f"Failed to pick color: {e}", "ui")
            messagebox.showerror("Error", f"Failed to pick color: {e}")
        
        finally:
            self.root.deiconify()
    
    # Advanced color picker removed per requirements
            
    def add_condition(self):
        """Add a new condition"""
        # Check if we have either a position or area selected
        if not self.selected_position and not self.selected_area:
            messagebox.showerror("Error", "Please select a position or area first.")
            return
            
        if not self.condition_type.get():
            messagebox.showerror("Error", "Please select a condition type (Color or Text).")
            return
            
        if self.condition_type.get() == 'color' and not self.selected_color:
            messagebox.showerror("Error", "Please pick a color first.")
            return
            
        if self.condition_type.get() == 'text' and not self.text_entry.get():
            messagebox.showerror("Error", "Please enter text to search for.")
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
        
        # Update the display to show the new condition
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
                return i
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
            conditions_in_groups.extend(group.conditions)
        
        # First add all the groups as parent items, except 'Default Group'
        group_display_index = 0
        for i, group in enumerate(self.condition_groups):
            if group.name != "Default Group":
                group_id = f"group_{group_display_index}"
                
                # Create friendly logic description
                logic_desc = self._get_logic_description(group.logic, group.n)
                
                # Insert group as parent
                self.unified_tree.insert('', 'end', iid=group_id, text='▼', 
                                       values=('Group', group.name, logic_desc),
                                       tags=('group',))
                
                # Add group conditions as children
                for j, condition in enumerate(group.conditions):
                    condition_id = f"group_{group_display_index}_cond_{j}"
                    condition_desc = self._format_condition_description(condition)
                    self.unified_tree.insert(group_id, 'end', iid=condition_id, text='',
                                           values=('Condition', condition_desc, ''),
                                           tags=('group_condition',))
                    
                group_display_index += 1
        
        # Then add standalone conditions (those not in any group)
        standalone_conditions = []
        
        # Debug information
        condition_ids = [id(c) for c in self.conditions]
        group_condition_ids = [id(c) for c in conditions_in_groups]
        
        print(f"All condition IDs: {condition_ids}")
        print(f"Group condition IDs: {group_condition_ids}")
        
        for condition in self.conditions:
            if not any(id(condition) == id(gc) for gc in conditions_in_groups):
                standalone_conditions.append(condition)
                
        print(f"Standalone conditions: {len(standalone_conditions)}, Total conditions: {len(self.conditions)}, In groups: {len(conditions_in_groups)}")
                
        for i, condition in enumerate(standalone_conditions):
            condition_desc = self._format_condition_description(condition)
            self.unified_tree.insert('', 'end', iid=f"standalone_{i}", text='',
                                   values=('Condition', condition_desc, ''),
                                   tags=('condition',))
            
            # Also add to hidden compatibility listbox
            self.conditions_listbox.insert(tk.END, condition_desc)
    
    def _ensure_conditions_consistency(self):
        """Ensure that self.conditions only contains standalone conditions (not in any group)."""
        print("Starting condition consistency check...")
        print(f"Before: Main conditions: {len(self.conditions)}, Group conditions: {sum(len(g.conditions) for g in self.condition_groups)}")

        # Build a set of all group condition ids
        group_condition_ids = set()
        for group in self.condition_groups:
            for condition in group.conditions:
                group_condition_ids.add(id(condition))

        # Remove any condition from self.conditions that is present in any group
        original_conditions = self.conditions[:]
        self.conditions = [cond for cond in original_conditions if id(cond) not in group_condition_ids]

        # Optionally, update group references to use the same object as in self.conditions if needed
        # (not strictly necessary if conditions are only in one place)

        print(f"After: Main conditions: {len(self.conditions)}, Group conditions: {sum(len(g.conditions) for g in self.condition_groups)}")
                
        # Configure tag appearance without background tints
        try:
            self.unified_tree.tag_configure('group', font=('Arial', 9, 'bold'))
            self.unified_tree.tag_configure('group_condition')
            self.unified_tree.tag_configure('condition')
        except Exception:
            pass
        
    def _format_condition_description(self, condition):
        """Format a condition into a readable description string"""
        # Position description
        if len(condition.position) == 4:
            x1, y1, x2, y2 = condition.position
            width = x2 - x1
            height = y2 - y1
            position_desc = f"area ({x1},{y1})-({x2},{y2}) [{width}x{height}]"
        else:
            position_desc = f"point ({condition.position[0]},{condition.position[1]})"
            
        # Type icon
        type_desc = "📊 Color" if condition.type == "color" else "📝 Text"
        
        # Value description
        if condition.type == "color":
            r, g, b = condition.value[:3]
            value_desc = f"RGB({r},{g},{b})"
        else:
            value_desc = f'"{condition.value}"'
        
        # Comparison description
        if condition.type == "color":
            comp_desc = f"matches (±{condition.tolerance})" if condition.comparator == "equals" else condition.comparator
        else:
            comp_desc = condition.comparator
                
        # Format the full condition string
        return f"{type_desc}: {value_desc} {comp_desc} at {position_desc}"
    
    def _get_logic_description(self, logic, n=None):
        """Get a friendly description of the logic type."""
        if logic == "all":
            return "ALL (AND)"
        elif logic == "any":
            return "ANY (OR)"
        elif logic == "n-of":
            return f"{n}-OF" if n else "N-OF"
        else:
            return logic.upper()
            
    def edit_condition(self):
        """Edit selected condition"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a condition to edit.")
            return
            
        index = selection[0]
        if index >= len(self.conditions):
            messagebox.showerror("Error", "Invalid condition selected.")
            return
            
        condition_to_edit = self.conditions[index]
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Condition")
        dialog.minsize(500, 400)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        self.center_window(dialog, 500, 400)
        
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
            position_text = f"Area: ({x1}, {y1}) to ({x2}, {y2})"
        else:
            position_text = f"Point: ({condition_to_edit.position[0]}, {condition_to_edit.position[1]})"
            
        ttk.Label(dialog, text=position_text).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Value
        ttk.Label(dialog, text="Value:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        value_var = tk.StringVar()
        if condition_to_edit.type == "color":
            value_var.set(f"RGB{condition_to_edit.value}")
            ttk.Label(dialog, textvariable=value_var).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
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
            try:
                # Update the condition
                condition_to_edit.type = type_var.get()
                condition_to_edit.comparator = comparator_var.get()
                condition_to_edit.tolerance = tolerance_var.get()
                if condition_to_edit.type == "text":
                    condition_to_edit.value = value_var.get()
                
                # Update display
                self.update_conditions_display()
                dialog.destroy()
                
                self.logger.log_action("EDIT_CONDITION", {
                    "type": condition_to_edit.type,
                    "comparator": condition_to_edit.comparator,
                    "tolerance": condition_to_edit.tolerance
                }, success=True)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save condition: {e}")
            
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
            if index < len(self.conditions):
                removed_condition = self.conditions.pop(index)
                self.update_conditions_display()
                
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
            self.tree_context_menu.add_command(label="Edit Group", command=lambda: self.edit_group_by_id(item))
            self.tree_context_menu.add_command(label="Delete Group", command=lambda: self.delete_group_by_id(item))
        elif "condition" in tags or "group_condition" in tags:
            self.tree_context_menu.add_command(label="Edit Condition", command=lambda: self.edit_condition_by_id(item))
            self.tree_context_menu.add_command(label="Remove Condition", command=lambda: self.remove_condition_by_id(item))
            if "condition" in tags:  # Only for standalone conditions
                self.tree_context_menu.add_command(label="Add to Group", command=lambda: self.add_condition_to_group_by_id(item))
                
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
        else:
            self.edit_condition_by_id(item)
    
    def toggle_item_collapse(self, item):
        """Toggle collapse/expand state of a tree item"""
        if self.unified_tree.item(item, "text") == "▼":
            self.unified_tree.item(item, text="▶")
            # Hide children
            for child in self.unified_tree.get_children(item):
                self.unified_tree.detach(child)
        else:
            self.unified_tree.item(item, text="▼")
            # Show children (they're still in memory, just detached)
            # This is a simplified implementation
            pass
    
    def edit_selected_item(self):
        """Edit the selected item in the tree"""
        selection = self.unified_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
            
        item = selection[0]
        item_type = self.unified_tree.item(item, "values")[0]
        
        if item_type == "Group":
            self.edit_group_by_id(item)
        else:
            self.edit_condition_by_id(item)
    
    def remove_selected_item(self):
        """Remove the selected item from the tree"""
        selection = self.unified_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to remove.")
            return
            
        item = selection[0]
        item_type = self.unified_tree.item(item, "values")[0]
        
        if item_type == "Group":
            self.delete_group_by_id(item)
        else:
            self.remove_condition_by_id(item)
            
    def edit_condition_by_id(self, item_id):
        """Edit condition by tree item ID"""
        # Extract condition info from item ID
        if item_id.startswith("standalone_"):
            index = int(item_id.split("_")[1])
            if index < len(self.conditions):
                self.edit_specific_condition(self.conditions[index])
        elif "_cond_" in item_id:
            # Group condition
            parts = item_id.split("_")
            group_index = int(parts[1])
            cond_index = int(parts[3])
            if group_index < len(self.condition_groups) and cond_index < len(self.condition_groups[group_index].conditions):
                self.edit_specific_condition(self.condition_groups[group_index].conditions[cond_index])
                
    def remove_condition_by_id(self, item_id):
        """Remove condition by tree item ID"""
        if item_id.startswith("standalone_"):
            index = int(item_id.split("_")[1])
            if index < len(self.conditions):
                removed_condition = self.conditions.pop(index)
                self.update_conditions_display()
                self.logger.log_action("REMOVE_CONDITION", {
                    "type": removed_condition.type,
                    "position": removed_condition.position
                }, success=True)
        elif "_cond_" in item_id:
            # Group condition
            parts = item_id.split("_")
            group_index = int(parts[1])
            cond_index = int(parts[3])
            if group_index < len(self.condition_groups) and cond_index < len(self.condition_groups[group_index].conditions):
                removed_condition = self.condition_groups[group_index].conditions.pop(cond_index)
                self.update_conditions_display()
                self.logger.log_action("REMOVE_GROUP_CONDITION", {
                    "group": self.condition_groups[group_index].name,
                    "type": removed_condition.type,
                    "position": removed_condition.position
                }, success=True)
                
    def add_condition_to_group_by_id(self, item_id):
        """Add standalone condition to a group"""
        if not item_id.startswith("standalone_"):
            return
            
        index = int(item_id.split("_")[1])
        if index >= len(self.conditions):
            return
            
        if not self.condition_groups:
            messagebox.showinfo("No Groups", "Please create a group first.")
            return
            
        # Select which group to add to
        dialog = tk.Toplevel(self.root)
        dialog.title("Add to Group")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        self.center_window(dialog, 400, 200)
        
        # Configure grid
        dialog.columnconfigure(0, weight=1)
        
        ttk.Label(dialog, text="Select Group:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        group_var = tk.StringVar()
        group_combo = ttk.Combobox(dialog, textvariable=group_var, state="readonly", width=30)
        group_combo["values"] = [g.name for g in self.condition_groups]
        group_combo.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        if self.condition_groups:
            group_combo.set(self.condition_groups[0].name)
            
        def add_condition_to_group():
            selected_group_name = group_var.get()
            if not selected_group_name:
                messagebox.showerror("Error", "Please select a group.")
                return
                
            # Find the group
            selected_group = None
            for group in self.condition_groups:
                if group.name == selected_group_name:
                    selected_group = group
                    break
                    
            if selected_group:
                # Move condition from standalone to group
                condition = self.conditions.pop(index)
                selected_group.conditions.append(condition)
                self.update_conditions_display()
                dialog.destroy()
                
                self.logger.log_action("ADD_CONDITION_TO_GROUP", {
                    "group": selected_group_name,
                    "condition_type": condition.type
                }, success=True)
            
        ttk.Button(dialog, text="Cancel", 
                  command=dialog.destroy).grid(row=2, column=0, padx=10, pady=20)
        
        ttk.Button(dialog, text="Add to Group", 
                  command=add_condition_to_group).grid(row=2, column=1, padx=10, pady=20)
    
    def edit_specific_condition(self, condition):
        """Edit a specific condition object"""
        # Find the condition in the main list to get its index
        found = False
        for i, main_condition in enumerate(self.conditions):
            if self._conditions_equal(condition, main_condition):
                # Temporarily set selection and call edit
                self.conditions_listbox.selection_clear(0, tk.END)
                self.conditions_listbox.selection_set(i)
                self.edit_condition()
                found = True
                break
                
        if found:
            return
        else:
            # Handle group conditions differently if needed
            messagebox.showinfo("Edit Condition", "Group condition editing not yet implemented.")
