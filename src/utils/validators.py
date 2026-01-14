"""
Input validation utilities
"""
import re
from datetime import datetime
from typing import List, Tuple, Optional


class Validators:
    """Input validation for the application"""
    
    @staticmethod
    def validate_ticker(ticker: str) -> bool:
        """
        Validate ticker symbol format
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if valid, False otherwise
        """
        if not ticker:
            return False
        # Basic validation: 1-5 uppercase letters, optionally followed by a dot and more letters
        pattern = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
        return bool(re.match(pattern, ticker.upper()))
    
    @staticmethod
    def validate_tickers(tickers: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of ticker symbols
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Tuple of (valid_tickers, invalid_tickers)
        """
        valid = []
        invalid = []
        
        for ticker in tickers:
            ticker = ticker.strip().upper()
            if Validators.validate_ticker(ticker):
                valid.append(ticker)
            else:
                invalid.append(ticker)
        
        return valid, invalid
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, Optional[str]]:
        """
        Validate date range
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start >= end:
                return False, "Start date must be before end date"
            
            if end > datetime.now():
                return False, "End date cannot be in the future"
            
            return True, None
        except ValueError as e:
            return False, f"Invalid date format: {str(e)}"
    
    @staticmethod
    def validate_strategy_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate strategy name
        
        Args:
            name: Strategy name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Strategy name cannot be empty"
        
        if len(name) > 100:
            return False, "Strategy name must be 100 characters or less"
        
        # Check for invalid characters (allow letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
            return False, "Strategy name contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_numeric_range(value: float, min_val: float, max_val: float, 
                               field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate numeric value is within range
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Name of the field for error message
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value < min_val or value > max_val:
            return False, f"{field_name} must be between {min_val} and {max_val}"
        
        return True, None
    
    @staticmethod
    def validate_percentage(value: float, field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate percentage value (0-100)
        
        Args:
            value: Percentage value
            field_name: Name of the field for error message
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return Validators.validate_numeric_range(value, 0, 100, field_name)
