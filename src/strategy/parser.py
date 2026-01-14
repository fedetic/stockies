"""
Strategy DSL parser for custom trading rules
"""
import re
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np


class StrategyParser:
    """Parses and validates strategy rules"""
    
    # Supported operators
    COMPARISON_OPERATORS = ['>=', '<=', '==', '!=', '>', '<']  # Order matters: longer operators first
    LOGICAL_OPERATORS = ['AND', 'OR', 'NOT']
    ARITHMETIC_OPERATORS = ['*', '/', '+', '-']
    
    # Supported indicators
    INDICATORS = [
        'sma', 'ema', 'wma', 'rsi', 'macd', 'macd_signal', 'macd_hist',
        'bb_upper', 'bb_middle', 'bb_lower', 'atr', 'stoch_k', 'stoch_d',
        'adx', 'obv', 'vwap', 'cci', 'roc', 'williams_r', 'momentum'
    ]
    
    # Supported variables
    VARIABLES = ['price', 'open', 'high', 'low', 'close', 'volume', 'entry_price']
    
    def __init__(self):
        pass
    
    def parse_condition(self, condition: str) -> Dict[str, Any]:
        """
        Parse a single condition string
        
        Args:
            condition: Condition string (e.g., "rsi(14) < 30")
            
        Returns:
            Dictionary with parsed condition components
        """
        condition = condition.strip()
        
        # Check for comparison operators
        for op in self.COMPARISON_OPERATORS:
            if op in condition:
                left, right = condition.split(op, 1)
                left = left.strip()
                right = right.strip()
                
                return {
                    'type': 'comparison',
                    'operator': op,
                    'left': self._parse_expression(left),
                    'right': self._parse_expression(right)
                }
        
        raise ValueError(f"Invalid condition: {condition}")
    
    def _parse_expression(self, expr: str) -> Dict[str, Any]:
        """
        Parse an expression (indicator, variable, value, or arithmetic operation)
        
        Args:
            expr: Expression string
            
        Returns:
            Dictionary with parsed expression
        """
        expr = expr.strip()
        
        # Check if it's a number
        try:
            value = float(expr)
            return {'type': 'value', 'value': value}
        except ValueError:
            pass
        
        # Check if it's a function call (indicator)
        func_match = re.match(r'(\w+)\((.*?)\)', expr)
        if func_match:
            func_name = func_match.group(1).lower()
            params_str = func_match.group(2)
            
            # Parse parameters
            params = []
            if params_str:
                param_parts = params_str.split(',')
                for param in param_parts:
                    param = param.strip()
                    # Try to parse as number
                    try:
                        params.append(float(param))
                    except ValueError:
                        # It's a variable reference
                        params.append(param.lower())
            
            if func_name in self.INDICATORS:
                return {
                    'type': 'indicator',
                    'name': func_name,
                    'params': params
                }
            else:
                raise ValueError(f"Unknown indicator: {func_name}")
        
        # Check if it's a variable
        if expr.lower() in self.VARIABLES:
            return {'type': 'variable', 'name': expr.lower()}
        
        # Check if it's an arithmetic expression (e.g., "entry_price * 0.95")
        for op in self.ARITHMETIC_OPERATORS:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left_str = parts[0].strip()
                    right_str = parts[1].strip()
                    
                    # Validate that both sides can be parsed
                    try:
                        left_expr = self._parse_expression(left_str)
                        right_expr = self._parse_expression(right_str)
                        
                        return {
                            'type': 'arithmetic',
                            'operator': op,
                            'left': left_expr,
                            'right': right_expr
                        }
                    except ValueError:
                        # If parsing fails, continue to try other operators
                        continue
        
        raise ValueError(f"Invalid expression: {expr}")
    
    def parse_rules(self, rules_text: str) -> List[Dict[str, Any]]:
        """
        Parse multiple rules connected by logical operators
        
        Args:
            rules_text: Rules text with AND/OR/NOT operators
            
        Returns:
            List of parsed rule dictionaries
        """
        # Split by AND/OR (keeping the operators)
        tokens = []
        current = []
        words = rules_text.split()
        
        for word in words:
            if word.upper() in self.LOGICAL_OPERATORS:
                if current:
                    tokens.append(' '.join(current))
                    current = []
                tokens.append(word.upper())
            else:
                current.append(word)
        
        if current:
            tokens.append(' '.join(current))
        
        # Parse each condition
        parsed_rules = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token in self.LOGICAL_OPERATORS:
                parsed_rules.append({'type': 'operator', 'operator': token})
            else:
                try:
                    parsed_condition = self.parse_condition(token)
                    parsed_rules.append(parsed_condition)
                except ValueError as e:
                    raise ValueError(f"Error parsing condition '{token}': {str(e)}")
            
            i += 1
        
        return parsed_rules
    
    def validate_strategy(self, strategy: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a complete strategy definition
        
        Args:
            strategy: Strategy dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['name', 'entry_rules', 'exit_rules']
        for field in required_fields:
            if field not in strategy:
                return False, f"Missing required field: {field}"
        
        # Validate strategy name
        if not strategy['name'] or len(strategy['name']) > 100:
            return False, "Strategy name must be 1-100 characters"
        
        # Validate entry rules
        try:
            if strategy['entry_rules']:
                self.parse_rules(strategy['entry_rules'])
        except Exception as e:
            return False, f"Invalid entry rules: {str(e)}"
        
        # Validate exit rules
        try:
            if strategy['exit_rules']:
                self.parse_rules(strategy['exit_rules'])
        except Exception as e:
            return False, f"Invalid exit rules: {str(e)}"
        
        # Validate position sizing
        if 'position_sizing' in strategy:
            pos_size = strategy['position_sizing']
            if 'method' not in pos_size:
                return False, "Position sizing method not specified"
            
            if pos_size['method'] not in ['fixed', 'percentage', 'risk_based']:
                return False, f"Invalid position sizing method: {pos_size['method']}"
        
        # Validate risk management
        if 'risk_management' in strategy:
            risk = strategy['risk_management']
            
            if 'stop_loss_pct' in risk:
                if not 0 < risk['stop_loss_pct'] <= 100:
                    return False, "Stop loss percentage must be between 0 and 100"
            
            if 'take_profit_pct' in risk:
                if not 0 < risk['take_profit_pct'] <= 1000:
                    return False, "Take profit percentage must be between 0 and 1000"
        
        return True, None
    
    @staticmethod
    def create_default_strategy() -> Dict[str, Any]:
        """
        Create a default strategy template
        
        Returns:
            Default strategy dictionary
        """
        return {
            'name': 'New Strategy',
            'description': '',
            'entry_rules': 'rsi(14) < 30 AND price > sma(200)',
            'exit_rules': 'rsi(14) > 70 OR price < entry_price * 0.95',
            'position_sizing': {
                'method': 'percentage',
                'value': 10  # 10% of capital per trade
            },
            'risk_management': {
                'stop_loss_pct': 5,  # 5% stop loss
                'take_profit_pct': 15,  # 15% take profit
                'trailing_stop': False,
                'trailing_stop_pct': None
            }
        }
