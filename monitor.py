"""
Screen monitoring system for autoclicker - coordinates detection and rule evaluation.
"""

import time
import threading
from typing import List, Callable, Optional
from config import Rule, Config
from detection import DetectionEngine
from logger import get_logger


class ScreenMonitor:
    """Monitors screen positions and evaluates rules for autoclicker automation"""
    
    def __init__(self, config: Config):
        """
        Initialize the screen monitor.
        
        Args:
            config: Configuration containing rules and settings
        """
        self.config = config
        self.detection_engine = DetectionEngine()
        self.logger = get_logger()
        self.is_monitoring = False
        self.is_processing_match = False  # Flag to pause monitoring during user intervention
        self.monitor_thread: Optional[threading.Thread] = None
        self.on_rule_matched: Optional[Callable] = None
        self.monitor_interval = 0.5  # Check every 500ms
        
    def set_rule_matched_callback(self, callback: Callable) -> None:
        """
        Set callback function to be called when a rule is matched.
        
        Args:
            callback: Function to call when rule matches. Should accept rule as parameter.
        """
        self.on_rule_matched = callback
        
    def start_monitoring(self) -> bool:
        """
        Start monitoring screen positions.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        if self.is_monitoring:
            print("Monitoring is already running")
            return False
            
        if not self.config.rules:
            print("No rules configured for monitoring")
            return False
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"Started monitoring {len(self.config.rules)} rule(s)")
        return True
        
    def stop_monitoring(self) -> bool:
        """
        Stop monitoring screen positions.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        if not self.is_monitoring:
            print("Monitoring is not running")
            return False
            
        self.is_monitoring = False
        
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
            
        print("Monitoring stopped")
        return True
        
    def is_running(self) -> bool:
        """
        Check if monitoring is currently running.
        
        Returns:
            True if monitoring is active, False otherwise
        """
        return self.is_monitoring
        
    def evaluate_rule(self, rule: Rule) -> bool:
        """
        Evaluate a rule by checking both condition groups and standalone conditions.
        Applies the main logic across group results and standalone conditions.
        """
        group_results = []
        if hasattr(rule, 'condition_groups') and rule.condition_groups:
            print(f"Evaluating rule with {len(rule.condition_groups)} condition groups")
            for group_idx, group in enumerate(rule.condition_groups):
                print(f"Evaluating group {group_idx+1}: {group.name} with {len(group.conditions)} conditions")
                condition_results = []
                for condition in group.conditions:
                    try:
                        result = self.detection_engine.evaluate_condition(condition)
                        condition_results.append(result)
                        self.logger.log_detection(
                            position=condition.position,
                            condition_type=condition.type,
                            result=result,
                            details={
                                "value": str(condition.value),
                                "comparator": condition.comparator,
                                "tolerance": condition.tolerance
                            }
                        )
                        print(f"Group {group_idx+1} - Condition {condition.type}:{condition.value} at {condition.position} = {result}")
                    except Exception as e:
                        self.logger.log_error(f"Error evaluating condition {condition.type} at {condition.position}", "monitor", e)
                        print(f"Error evaluating condition: {e}")
                        condition_results.append(False)
                group_result = self._apply_rule_logic(group.logic, condition_results, group.n)
                group_results.append(group_result)
                print(f"Group {group_idx+1} ({group.name}) with logic '{group.logic}' result: {group_result}")

        # Evaluate standalone conditions (not in any group)
        standalone_results = []
        if hasattr(rule, 'conditions') and rule.conditions:
            print(f"Evaluating {len(rule.conditions)} standalone conditions")
            for condition in rule.conditions:
                try:
                    result = self.detection_engine.evaluate_condition(condition)
                    standalone_results.append(result)
                    self.logger.log_detection(
                        position=condition.position,
                        condition_type=condition.type,
                        result=result,
                        details={
                            "value": str(condition.value),
                            "comparator": condition.comparator,
                            "tolerance": condition.tolerance
                        }
                    )
                    print(f"Standalone condition {condition.type}:{condition.value} at {condition.position} = {result}")
                except Exception as e:
                    self.logger.log_error(f"Error evaluating standalone condition {condition.type} at {condition.position}", "monitor", e)
                    print(f"Error evaluating standalone condition: {e}")
                    standalone_results.append(False)

        # Combine group results and standalone condition results
        all_results = group_results + standalone_results
        print(f"Combining {len(group_results)} group results and {len(standalone_results)} standalone results")

        # Determine which logic to use
        main_logic = getattr(rule, 'group_logic', 'any')
        n = getattr(rule, 'n', None)
        if main_logic is None:
            main_logic = 'any'

        # If there are no results, rule is not satisfied
        if not all_results:
            print("No group or standalone results to evaluate")
            return False

        # Apply main logic across all results
        final_result = self._apply_rule_logic(main_logic, all_results, n)
        print(f"Final rule result with '{main_logic.upper()}' logic across {len(all_results)} items: {final_result}")
        return final_result
        
    def _monitor_loop(self) -> None:
        """
        Main monitoring loop that runs in a separate thread.
        """
        print("Monitor loop started")
        
        while self.is_monitoring:
            try:
                # Skip monitoring if we're processing a match (during delay/popup)
                if self.is_processing_match:
                    time.sleep(0.1)  # Short sleep to avoid busy waiting
                    continue
                
                # Check each rule
                for rule in self.config.rules:
                    if not self.is_monitoring or self.is_processing_match:
                        break
                        
                    if self.evaluate_rule(rule):
                        print(f"Rule matched! Logic: {rule.logic}")
                        
                        # Set processing flag to pause further monitoring
                        self.is_processing_match = True
                        
                        # Call the callback if set
                        if self.on_rule_matched:
                            try:
                                self.on_rule_matched(rule)
                            except Exception as e:
                                print(f"Error in rule matched callback: {e}")
                                # Reset flag on error
                                self.is_processing_match = False
                        
                        # Break out of rule checking loop after first match
                        break
                        
                # Wait before next check (only if not processing)
                if not self.is_processing_match:
                    time.sleep(self.monitor_interval)
                
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(self.monitor_interval)
                
        print("Monitor loop ended")
    
    def resume_monitoring(self):
        """Resume monitoring after user intervention is complete"""
        self.is_processing_match = False
        print("Monitoring resumed after user intervention")
        
    def _apply_rule_logic(self, logic: str, condition_results: List[bool], n: Optional[int] = None) -> bool:
        """
        Apply the specified logic to condition results.
        
        Args:
            logic: Type of logic ('any', 'all', 'n-of')
            condition_results: List of boolean results from condition evaluations
            n: Required number of conditions for 'n-of' logic
            
        Returns:
            True if logic is satisfied, False otherwise
        """
        if not condition_results:
            print(f"WARNING: No condition results to evaluate for {logic} logic")
            return False
            
        # Add detailed debugging for each logic type
        if logic.lower() == 'any':
            result = any(condition_results)
            print(f"ANY (OR) logic with {condition_results} = {result}")
            return result
        elif logic.lower() == 'all':
            result = all(condition_results)
            print(f"ALL (AND) logic with {condition_results} = {result}")
            return result
        elif logic.lower() == 'n-of':
            if n is None or n <= 0:
                print(f"Invalid n value '{n}' for n-of logic")
                return False
            true_count = sum(1 for r in condition_results if r)  # More reliable than sum()
            result = true_count >= n
            print(f"N-OF logic with n={n}, results={condition_results}, true_count={true_count}, result={result}")
            return result
        else:
            print(f"Unknown logic type: '{logic}' - defaulting to ANY logic")
            # Default to ANY logic as a fallback
            result = any(condition_results)
            print(f"Defaulted to ANY logic with {condition_results} = {result}")
            return result
            
    def update_config(self, new_config: Config) -> None:
        """
        Update the monitoring configuration.
        
        Args:
            new_config: New configuration to use
        """
        was_monitoring = self.is_monitoring
        
        # Stop monitoring if running
        if was_monitoring:
            self.stop_monitoring()
            
        # Update config
        self.config = new_config
        
        # Restart monitoring if it was running
        if was_monitoring:
            self.start_monitoring()
            
        print("Configuration updated")
        
    def get_status(self) -> dict:
        """
        Get current status of the monitor.
        
        Returns:
            Dictionary containing status information
        """
        return {
            'is_monitoring': self.is_monitoring,
            'rules_count': len(self.config.rules),
            'monitor_interval': self.monitor_interval,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False
        }
