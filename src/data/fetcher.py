"""
Stock data fetcher using Yahoo Finance
"""
import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .cache import CacheManager
from config.settings import YAHOO_FINANCE_TIMEOUT, DEFAULT_TIMEFRAME


class DataFetcher:
    """Fetches stock data from Yahoo Finance with caching"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache = cache_manager or CacheManager()
    
    def get_historical_data(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str,
        interval: str = DEFAULT_TIMEFRAME,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1d, 1h, etc.)
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with historical data (columns: Open, High, Low, Close, Volume, Adj Close)
        """
        ticker = ticker.upper()
        
        # Try cache first
        if use_cache and interval == '1d':
            cached_data = self.cache.get_historical_prices(ticker, start_date, end_date)
            if cached_data is not None:
                return cached_data
        
        # Fetch from Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(
                start=start_date,
                end=end_date,
                interval=interval,
                timeout=YAHOO_FINANCE_TIMEOUT
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # Standardize column names - replace spaces with underscores
            df.columns = [col.replace(' ', '_') if ' ' in col else col for col in df.columns]
            
            # Ensure index is named 'Date' for consistency
            if df.index.name is None or df.index.name.lower() == 'date':
                df.index.name = 'Date'
            
            # Ensure we have the basic OHLCV columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = 0
            
            # Add Adj_Close if not present (handle both 'Adj Close' and 'Adj_Close')
            if 'Adj_Close' not in df.columns:
                if 'Adj Close' in df.columns:
                    df['Adj_Close'] = df['Adj Close']
                else:
                    df['Adj_Close'] = df['Close']
            
            # Cache the data (only for daily interval)
            if interval == '1d':
                self.cache.save_historical_prices(ticker, df)
            
            return df
        
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_info(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get stock information
        
        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary with stock info
        """
        ticker = ticker.upper()
        
        # Try cache first
        if use_cache:
            cached_info = self.cache.get_stock_info(ticker)
            if cached_info is not None:
                return cached_info
        
        # Fetch from Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Cache the data
            self.cache.save_stock_info(ticker, info)
            
            return info
        
        except Exception as e:
            print(f"Error fetching info for {ticker}: {str(e)}")
            return {}
    
    def get_fundamental_data(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get fundamental data (financial statements)
        
        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary with fundamental data (income_statement, balance_sheet, cash_flow)
        """
        ticker = ticker.upper()
        
        # Try cache first
        if use_cache:
            cached_data = self.cache.get_fundamental_data(ticker)
            if cached_data is not None:
                return cached_data
        
        # Fetch from Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            
            fundamental_data = {
                'income_statement': stock.financials.to_dict() if hasattr(stock, 'financials') and not stock.financials.empty else {},
                'balance_sheet': stock.balance_sheet.to_dict() if hasattr(stock, 'balance_sheet') and not stock.balance_sheet.empty else {},
                'cash_flow': stock.cashflow.to_dict() if hasattr(stock, 'cashflow') and not stock.cashflow.empty else {},
            }
            
            # Cache the data
            self.cache.save_fundamental_data(ticker, fundamental_data)
            
            return fundamental_data
        
        except Exception as e:
            print(f"Error fetching fundamental data for {ticker}: {str(e)}")
            return {
                'income_statement': {},
                'balance_sheet': {},
                'cash_flow': {}
            }
    
    def get_multiple_stocks(
        self, 
        tickers: List[str], 
        start_date: str, 
        end_date: str,
        interval: str = DEFAULT_TIMEFRAME
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple stocks
        
        Args:
            tickers: List of stock ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1d, 1h, etc.)
            
        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}
        
        for ticker in tickers:
            df = self.get_historical_data(ticker, start_date, end_date, interval)
            if not df.empty:
                results[ticker.upper()] = df
        
        return results
    
    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the latest price for a stock
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Latest price or None if not available
        """
        ticker = ticker.upper()
        
        try:
            stock = yf.Ticker(ticker)
            
            # Try to get from info first
            info = stock.info
            if 'regularMarketPrice' in info:
                return float(info['regularMarketPrice'])
            elif 'currentPrice' in info:
                return float(info['currentPrice'])
            
            # Fallback to latest historical data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            df = self.get_historical_data(ticker, start_date, end_date, use_cache=False)
            if not df.empty:
                return float(df['Close'].iloc[-1])
            
            return None
        
        except Exception as e:
            print(f"Error fetching latest price for {ticker}: {str(e)}")
            return None
    
    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate that a ticker exists and has data
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if ticker is valid, False otherwise
        """
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            # Check if we got valid info
            return 'symbol' in info or 'shortName' in info
        
        except Exception:
            return False
