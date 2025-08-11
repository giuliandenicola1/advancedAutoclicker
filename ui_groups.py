import tkinter as tk
from tkinter import ttk, messagebox
from config import ConditionGroup


class UIGroupsMixin:
    """
    Mixin class for group management functionality.
    Contains methods for creating, editing, and managing condition groups.
    """
    
    def create_group(self):
        """Create a new condition group"""
        # Ask for group name and logic
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Condition Group")
        dialog.minsize(500, 500)    # Set minimum size to ensure visibility
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        self.center_window(dialog, 500, 500)
        
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
            logic_var.set("all")
            n_entry.config(state="disabled")
            
        def set_any():
            logic_var.set("any") 
            n_entry.config(state="disabled")
            
        def set_n_of():
            logic_var.set("n-of")
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
                messagebox.showerror("Error", "Please enter a group name.")
                return
                
            logic = logic_var.get()
            n = None
            
            if logic == "n-of":
                try:
                    n = int(n_var.get())
                    if n < 1:
                        messagebox.showerror("Error", "N must be at least 1.")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number for N.")
                    return
                    
            # Check if group name already exists
            for group in self.condition_groups:
                if group.name == name:
                    messagebox.showerror("Error", f"A group named '{name}' already exists.")
                    return
                    
            # Create the group
            new_group = ConditionGroup(
                name=name,
                logic=logic,
                n=n,
                conditions=[]
            )
            
            self.condition_groups.append(new_group)
            self.update_conditions_display()
            self.update_groups_display()
            dialog.destroy()
            
            self.logger.log_action("CREATE_GROUP", {
                "name": name,
                "logic": logic,
                "n": n
            }, success=True)
        
        # Add buttons using direct grid placement like the Select Point/Area buttons
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
            # Get selection from tree
            selection = self.unified_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a group to edit.")
                return
            item = selection[0]
            if not item.startswith("group_"):
                messagebox.showwarning("Invalid Selection", "Please select a group to edit.")
                return
            group_index = int(item.split("_")[1])
            
        if group_index >= len(self.condition_groups):
            messagebox.showerror("Error", "Invalid group selected.")
            return
            
        group = self.condition_groups[group_index]
        
        # Create dialog similar to create_group but pre-filled
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Condition Group")
        dialog.minsize(500, 400)    # Set minimum size
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        self.center_window(dialog, 500, 400)
        
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
            logic_var.set("all")
            n_entry.config(state="disabled")
            
        def set_any():
            logic_var.set("any")
            n_entry.config(state="disabled")
            
        def set_n_of():
            logic_var.set("n-of")
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
                messagebox.showerror("Error", "Please enter a group name.")
                return
                
            logic = logic_var.get()
            n = None
            
            if logic == "n-of":
                try:
                    n = int(n_var.get())
                    if n < 1:
                        messagebox.showerror("Error", "N must be at least 1.")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number for N.")
                    return
                    
            # Check if group name already exists (except for current group)
            for i, existing_group in enumerate(self.condition_groups):
                if i != group_index and existing_group.name == name:
                    messagebox.showerror("Error", f"A group named '{name}' already exists.")
                    return
                    
            # Update the group
            old_name = group.name
            group.name = name
            group.logic = logic
            group.n = n
            
            self.update_conditions_display()
            self.update_groups_display()
            dialog.destroy()
            
            self.logger.log_action("EDIT_GROUP", {
                "old_name": old_name,
                "new_name": name,
                "logic": logic,
                "n": n
            }, success=True)
            
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
            selection = self.unified_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a group to delete.")
                return
            item = selection[0]
            if not item.startswith("group_"):
                messagebox.showwarning("Invalid Selection", "Please select a group to delete.")
                return
            group_index = int(item.split("_")[1])
            
        # Validate index
        if group_index >= len(self.condition_groups):
            messagebox.showerror("Error", "Invalid group selected.")
            return
            
        # Confirm deletion
        group_name = self.condition_groups[group_index].name
        num_conditions = len(self.condition_groups[group_index].conditions)
        
        if messagebox.askyesno("Confirm Delete", 
                             f"Delete group '{group_name}' and all its {num_conditions} conditions?"):
            removed_group = self.condition_groups.pop(group_index)
            self.update_conditions_display()
            self.update_groups_display()
            
            self.logger.log_action("DELETE_GROUP", {
                "name": removed_group.name,
                "conditions_count": len(removed_group.conditions)
            }, success=True)
            
    def add_to_group(self):
        """Add selected condition to a group"""
        # Check both the unified tree and the legacy listbox for selection
        selection = self.unified_tree.selection()
        condition_selection = self.conditions_listbox.curselection()
        
        # If we have a tree selection, use that preferentially
        if selection:
            item = selection[0]
            if not item.startswith("standalone_"):
                messagebox.showwarning("Invalid Selection", "Please select a standalone condition to add to a group.")
                return
            condition_index = int(item.split("_")[1])
        elif condition_selection:
            condition_index = condition_selection[0]
        else:
            messagebox.showwarning("No Selection", "Please select a condition to add to a group.")
            return
            
        if condition_index >= len(self.conditions):
            messagebox.showerror("Error", "Invalid condition selected.")
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
        
        # Use grid instead of pack
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
                condition = self.conditions.pop(condition_index)
                selected_group.conditions.append(condition)
                self.update_conditions_display()
                self.update_groups_display()
                dialog.destroy()
                
                self.logger.log_action("ADD_CONDITION_TO_GROUP", {
                    "group": selected_group_name,
                    "condition_type": condition.type
                }, success=True)
            
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
            self.groups_listbox.insert('', 'end', iid=str(i), values=(
                group.name, 
                group.logic + (f"({group.n})" if group.n else ""), 
                len(group.conditions)
            ))
        
        # Now update the main unified tree
        self.update_conditions_display()
    
    def edit_group_by_id(self, item_id):
        """Edit group by tree item ID"""
        if not item_id.startswith("group_"):
            return
        group_index = int(item_id.split("_")[1])
        self.edit_group(group_index)
        
    def delete_group_by_id(self, item_id):
        """Delete group by tree item ID"""
        if not item_id.startswith("group_"):
            return
        group_index = int(item_id.split("_")[1])
        self.delete_group(group_index)
        
    def remove_from_group(self):
        """Remove a condition from its group but keep it in the standalone list"""
        selection = self.unified_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a group condition to remove.")
            return
            
        item = selection[0]
        
        # Only proceed if it's a group condition
        if item.startswith("group_") and "_cond_" in item:
            parts = item.split("_")
            group_index = int(parts[1])
            cond_index = int(parts[3])
            
            if group_index < len(self.condition_groups) and cond_index < len(self.condition_groups[group_index].conditions):
                # Move condition from group back to standalone
                condition = self.condition_groups[group_index].conditions.pop(cond_index)
                self.conditions.append(condition)
                self.update_conditions_display()
                self.update_groups_display()
                
                self.logger.log_action("REMOVE_FROM_GROUP", {
                    "group": self.condition_groups[group_index].name,
                    "condition_type": condition.type
                }, success=True)
        else:
            messagebox.showwarning("Invalid Selection", "Please select a condition within a group.")
                    
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
            messagebox.showinfo("Group Details", f"Group '{group.name}' has no conditions.")
            return
            
        # Create a detailed view of the group's conditions
        details = tk.Toplevel(self.root)
        details.title(f"Group Details: {group.name}")
        details.transient(self.root)
        
        # Center the dialog
        self.center_window(details, 500, 400)
        
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
            logic_explanation = f"Exactly {group.n} out of {len(group.conditions)} conditions must match"
            
        ttk.Label(header_frame, text=f"Group: {group.name}", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"Logic: {logic_explanation}").pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"Conditions: {len(group.conditions)}").pack(anchor=tk.W)
        
        # List of conditions
        cond_frame = ttk.LabelFrame(details, text="Conditions in this group")
        cond_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        conditions_list = tk.Listbox(cond_frame)
        conditions_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for i, condition in enumerate(group.conditions):
            description = self._format_condition_description(condition)
            conditions_list.insert(tk.END, f"{i+1}. {description}")
        
        ttk.Button(details, text="Close", command=details.destroy).pack(pady=10)
