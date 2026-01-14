"""
Advanced rules engine for executing trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from .indicators import Indicators
from .parser import StrategyParser


class RulesEngine:
    """Executes trading rules on historical data"""
    
    def __init__(self):
        self.parser = StrategyParser()
    
    def apply_strategy(
        self,
        df: pd.DataFrame,
        strategy: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Apply a strategy to historical data and generate signals
        
        Args:
            df: DataFrame with OHLCV data
            strategy: Strategy dictionary with rules
            
        Returns:
            DataFrame with signals added (entry_signal, exit_signal columns)
        """
        df = df.copy()
        
        # Calculate all indicators first
        df = Indicators.calculate_all(df)
        
        # Generate entry signals
        entry_rules = strategy.get('entry_rules', '')
        if entry_rules:
            df['entry_signal'] = self._evaluate_rules(df, entry_rules)
        else:
            df['entry_signal'] = False
        
        # Generate exit signals
        exit_rules = strategy.get('exit_rules', '')
        if exit_rules:
            df['exit_signal'] = self._evaluate_rules(df, exit_rules, include_entry_price=True)
        else:
            df['exit_signal'] = False
        
        return df
    
    def _evaluate_rules(
        self,
        df: pd.DataFrame,
        rules_text: str,
        include_entry_price: bool = False
    ) -> pd.Series:
        """
        Evaluate rules and return a boolean series
        
        Args:
            df: DataFrame with price data and indicators
            rules_text: Rules text to evaluate
            include_entry_price: Whether to include entry_price in evaluation context
            
        Returns:
            Boolean series indicating where rules are satisfied
        """
        try:
            parsed_rules = self.parser.parse_rules(rules_text)
        except Exception as e:
            print(f"Error parsing rules: {str(e)}")
            return pd.Series(False, index=df.index)
        
        # Evaluate each rule component
        result_stack = []
        
        for rule in parsed_rules:
            if rule['type'] == 'operator':
                # Handle logical operators
                operator = rule['operator']
                
                if operator == 'NOT':
                    if result_stack:
                        result_stack[-1] = ~result_stack[-1]
                elif operator == 'AND':
                    if len(result_stack) >= 2:
                        right = result_stack.pop()
                        left = result_stack.pop()
                        result_stack.append(left & right)
                elif operator == 'OR':
                    if len(result_stack) >= 2:
                        right = result_stack.pop()
                        left = result_stack.pop()
                        result_stack.append(left | right)
            
            elif rule['type'] == 'comparison':
                # Evaluate comparison
                left_series = self._evaluate_expression(df, rule['left'], include_entry_price)
                right_series = self._evaluate_expression(df, rule['right'], include_entry_price)
                
                operator = rule['operator']
                
                if operator == '>':
                    result = left_series > right_series
                elif operator == '<':
                    result = left_series < right_series
                elif operator == '>=':
                    result = left_series >= right_series
                elif operator == '<=':
                    result = left_series <= right_series
                elif operator == '==':
                    result = left_series == right_series
                elif operator == '!=':
                    result = left_series != right_series
                else:
                    result = pd.Series(False, index=df.index)
                
                result_stack.append(result)
        
        # Return final result
        if result_stack:
            return result_stack[0].fillna(False)
        else:
            return pd.Series(False, index=df.index)
    
    def _evaluate_expression(
        self,
        df: pd.DataFrame,
        expr: Dict[str, Any],
        include_entry_price: bool = False
    ) -> pd.Series:
        """
        Evaluate a single expression and return a series
        
        Args:
            df: DataFrame with price data and indicators
            expr: Parsed expression dictionary
            include_entry_price: Whether to include entry_price in evaluation context
            
        Returns:
            Series with expression values
        """
        expr_type = expr['type']
        
        if expr_type == 'value':
            # Constant value
            return pd.Series(expr['value'], index=df.index)
        
        elif expr_type == 'arithmetic':
            # Arithmetic operation (e.g., entry_price * 0.95)
            left_series = self._evaluate_expression(df, expr['left'], include_entry_price)
            right_series = self._evaluate_expression(df, expr['right'], include_entry_price)
            operator = expr['operator']
            
            if operator == '*':
                return left_series * right_series
            elif operator == '/':
                return left_series / right_series
            elif operator == '+':
                return left_series + right_series
            elif operator == '-':
                return left_series - right_series
            else:
                return pd.Series(np.nan, index=df.index)
        
        elif expr_type == 'variable':
            # Variable reference
            var_name = expr['name']
            
            # Map variable names to DataFrame columns
            var_map = {
                'price': 'Close',
                'close': 'Close',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'volume': 'Volume'
            }
            
            col_name = var_map.get(var_name, var_name)
            
            if col_name in df.columns:
                return df[col_name]
            elif var_name == 'entry_price' and include_entry_price:
                # Entry price will be handled during backtesting
                return pd.Series(np.nan, index=df.index)
            else:
                return pd.Series(np.nan, index=df.index)
        
        elif expr_type == 'indicator':
            # Indicator calculation
            indicator_name = expr['name']
            params = expr['params']
            
            # Map indicator names to calculations
            if indicator_name == 'sma':
                if params and isinstance(params[0], (int, float)):
                    period = int(params[0])
                    col_name = f'SMA_{period}'
                    if col_name in df.columns:
                        return df[col_name]
                    else:
                        return Indicators.sma(df['Close'], period)
            
            elif indicator_name == 'ema':
                if params and isinstance(params[0], (int, float)):
                    period = int(params[0])
                    col_name = f'EMA_{period}'
                    if col_name in df.columns:
                        return df[col_name]
                    else:
                        return Indicators.ema(df['Close'], period)
            
            elif indicator_name == 'rsi':
                period = int(params[0]) if params else 14
                col_name = f'RSI_{period}'
                if col_name in df.columns:
                    return df[col_name]
                else:
                    return Indicators.rsi(df['Close'], period)
            
            elif indicator_name == 'macd':
                if 'MACD' in df.columns:
                    return df['MACD']
                else:
                    macd, _, _ = Indicators.macd(df['Close'])
                    return macd
            
            elif indicator_name == 'macd_signal':
                if 'MACD_Signal' in df.columns:
                    return df['MACD_Signal']
                else:
                    _, signal, _ = Indicators.macd(df['Close'])
                    return signal
            
            elif indicator_name == 'macd_hist':
                if 'MACD_Hist' in df.columns:
                    return df['MACD_Hist']
                else:
                    _, _, hist = Indicators.macd(df['Close'])
                    return hist
            
            elif indicator_name == 'bb_upper':
                if 'BB_Upper' in df.columns:
                    return df['BB_Upper']
            
            elif indicator_name == 'bb_lower':
                if 'BB_Lower' in df.columns:
                    return df['BB_Lower']
            
            elif indicator_name == 'atr':
                period = int(params[0]) if params else 14
                col_name = f'ATR_{period}'
                if col_name in df.columns:
                    return df[col_name]
                else:
                    return Indicators.atr(df['High'], df['Low'], df['Close'], period)
            
            elif indicator_name == 'adx':
                if 'ADX_14' in df.columns:
                    return df['ADX_14']
            
            elif indicator_name == 'stoch_k':
                if 'Stoch_K' in df.columns:
                    return df['Stoch_K']
            
            elif indicator_name == 'stoch_d':
                if 'Stoch_D' in df.columns:
                    return df['Stoch_D']
            
            # Return NaN if indicator not found
            return pd.Series(np.nan, index=df.index)
        
        return pd.Series(np.nan, index=df.index)
    
    def get_position_size(
        self,
        strategy: Dict[str, Any],
        capital: float,
        price: float,
        atr: Optional[float] = None
    ) -> int:
        """
        Calculate position size based on strategy rules
        
        Args:
            strategy: Strategy dictionary
            capital: Available capital
            price: Current stock price
            atr: Average True Range (for risk-based sizing)
            
        Returns:
            Number of shares to buy
        """
        pos_sizing = strategy.get('position_sizing', {})
        method = pos_sizing.get('method', 'percentage')
        value = pos_sizing.get('value', 10)
        
        if method == 'fixed':
            # Fixed dollar amount
            shares = int(value / price)
        
        elif method == 'percentage':
            # Percentage of capital
            allocation = capital * (value / 100)
            shares = int(allocation / price)
        
        elif method == 'risk_based':
            # Risk-based position sizing using ATR
            if atr and atr > 0:
                risk_amount = capital * (value / 100)  # value is risk percentage
                risk_per_share = atr * 2  # 2x ATR for risk
                shares = int(risk_amount / risk_per_share)
            else:
                # Fallback to percentage
                allocation = capital * (value / 100)
                shares = int(allocation / price)
        
        else:
            shares = 0
        
        return max(shares, 0)
