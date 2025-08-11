from dataclasses import dataclass
from typing import List, Literal, Optional, Union

@dataclass
class Condition:
    """Represents a single detection condition"""
    type: Literal['color', 'text']
    position: Union[tuple[int, int], tuple[int, int, int, int]]  # (x, y) for point or (x1, y1, x2, y2) for area
    value: Union[tuple[int, int, int], str]  # RGB tuple for color, string for text
    comparator: Literal['equals', 'contains', 'similar'] = 'equals'
    tolerance: int = 10  # Tolerance for color matching (0-100)
    
    def is_area_selection(self) -> bool:
        """Check if this condition uses area selection (4 coordinates)"""
        return len(self.position) == 4

@dataclass
class ConditionGroup:
    """Represents a group of conditions with their own logic"""
    conditions: List[Condition]
    logic: Literal['any', 'all', 'n-of'] = 'all'  # Default to 'all' for groups
    n: Optional[int] = None  # Required for 'n-of' logic
    name: str = "Group"  # Optional name for the group

@dataclass
class Rule:
    """Represents a rule with condition groups and separate click position"""
    click_position: tuple[int, int]  # Separate click position (x, y) - required field first
    condition_groups: List[ConditionGroup]
    group_logic: Literal['any', 'all'] = 'any'  # Logic between groups
    
    # Legacy support for single conditions (backward compatibility)
    conditions: Optional[List[Condition]] = None
    logic: Optional[Literal['any', 'all', 'n-of']] = None
    n: Optional[int] = None
    
    def __post_init__(self):
        """Convert legacy conditions to new group format"""
        if self.conditions is not None and not self.condition_groups:
            # Convert old format to new format
            legacy_group = ConditionGroup(
                conditions=self.conditions,
                logic=self.logic or 'any',
                n=self.n,
                name="Legacy Group"
            )
            self.condition_groups = [legacy_group]

@dataclass
class Config:
    """Main configuration for the autoclicker"""
    rules: List[Rule] = None
    delay: int = 0  # Delay in seconds before clicking
    popup: bool = True  # Show confirmation popup
    version: str = "1.0"  # Configuration version

    def __post_init__(self):
        if self.rules is None:
            self.rules = []
    
    def add_rule(self, rule: Rule):
        """Add a rule to the configuration"""
        self.rules.append(rule)
    
    def remove_rule(self, index: int):
        """Remove a rule by index"""
        if 0 <= index < len(self.rules):
            del self.rules[index]
    
    def get_rule_count(self) -> int:
        """Get the number of rules"""
        return len(self.rules)
    
    def validate(self) -> bool:
        """Validate the configuration"""
        if not self.rules:
            return False
        
        for rule in self.rules:
            if not rule.conditions:
                return False
            
            if rule.logic == 'n-of' and (rule.n is None or rule.n <= 0 or rule.n > len(rule.conditions)):
                return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary"""
        rules_data = []
        for rule in self.rules:
            rule_data = {
                'click_position': rule.click_position,
                'group_logic': rule.group_logic,
                'condition_groups': []
            }
            
            # Convert each condition group
            for group in rule.condition_groups:
                group_data = {
                    'name': group.name,
                    'logic': group.logic,
                    'n': group.n,
                    'conditions': []
                }
                
                # Convert each condition in the group
                for condition in group.conditions:
                    condition_data = {
                        'type': condition.type,
                        'position': condition.position,
                        'value': condition.value if not isinstance(condition.value, tuple) else list(condition.value),
                        'comparator': condition.comparator,
                        'tolerance': condition.tolerance
                    }
                    group_data['conditions'].append(condition_data)
                
                rule_data['condition_groups'].append(group_data)
                
            rules_data.append(rule_data)
            
        return {
            'version': self.version,
            'delay': self.delay,
            'popup': self.popup,
            'rules': rules_data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create a configuration from a dictionary"""
        config = cls()
        config.version = data.get('version', '1.0')
        config.delay = data.get('delay', 0)
        config.popup = data.get('popup', True)
        
        # Initialize rules list
        config.rules = []
        
        # Process each rule
        for rule_data in data.get('rules', []):
            rule = Rule(
                click_position=tuple(rule_data['click_position']),
                condition_groups=[],
                group_logic=rule_data.get('group_logic', 'any')
            )
            
            # Process each condition group
            for group_data in rule_data.get('condition_groups', []):
                group = ConditionGroup(
                    conditions=[],
                    logic=group_data.get('logic', 'all'),
                    n=group_data.get('n'),
                    name=group_data.get('name', 'Group')
                )
                
                # Process each condition in the group
                for condition_data in group_data.get('conditions', []):
                    # Handle RGB values (convert lists back to tuples)
                    value = condition_data.get('value')
                    if isinstance(value, list) and len(value) == 3:
                        value = tuple(value)
                        
                    condition = Condition(
                        type=condition_data.get('type', 'color'),
                        position=tuple(condition_data.get('position')),
                        value=value,
                        comparator=condition_data.get('comparator', 'equals'),
                        tolerance=condition_data.get('tolerance', 10)
                    )
                    group.conditions.append(condition)
                    
                rule.condition_groups.append(group)
                
            config.rules.append(rule)
            
        return config
