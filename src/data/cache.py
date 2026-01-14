"""
Database caching layer for stock data
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
import json
from pathlib import Path

from config.settings import CACHE_DB_PATH, CACHE_EXPIRY_DAYS


class CacheManager:
    """Manages SQLite cache for stock data"""
    
    def __init__(self, db_path: Path = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Historical prices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                adj_close REAL,
                created_at TEXT NOT NULL,
                UNIQUE(ticker, date)
            )
        ''')
        
        # Fundamental data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fundamental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Stock info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                info TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_date ON historical_prices(ticker, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON fundamental_data(ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_ticker ON stock_info(ticker)')
        
        conn.commit()
        conn.close()
    
    def get_historical_prices(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Get cached historical prices
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with historical prices or None if not in cache/expired
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Check if we have recent data
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MIN(created_at) as oldest
                FROM historical_prices
                WHERE ticker = ? AND date >= ? AND date <= ?
            ''', (ticker, start_date, end_date))
            
            result = cursor.fetchone()
            if not result[0]:
                return None
            
            # Check if data is expired
            oldest_date = datetime.fromisoformat(result[0])
            if datetime.now() - oldest_date > timedelta(days=CACHE_EXPIRY_DAYS):
                return None
            
            # Retrieve data
            df = pd.read_sql_query('''
                SELECT date, open, high, low, close, volume, adj_close
                FROM historical_prices
                WHERE ticker = ? AND date >= ? AND date <= ?
                ORDER BY date
            ''', conn, params=(ticker, start_date, end_date))
            
            if df.empty:
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        finally:
            conn.close()
    
    def save_historical_prices(self, ticker: str, df: pd.DataFrame):
        """
        Save historical prices to cache
        
        Args:
            ticker: Stock ticker symbol
            df: DataFrame with historical prices (index: date, columns: open, high, low, close, volume, adj_close)
        """
        if df.empty:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            created_at = datetime.now().isoformat()
            
            # Prepare data
            df_reset = df.reset_index()
            df_reset['date'] = df_reset['date'].dt.strftime('%Y-%m-%d')
            
            # Insert or replace data
            for _, row in df_reset.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_prices
                    (ticker, date, open, high, low, close, volume, adj_close, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticker,
                    row['date'],
                    row.get('Open', row.get('open')),
                    row.get('High', row.get('high')),
                    row.get('Low', row.get('low')),
                    row.get('Close', row.get('close')),
                    row.get('Volume', row.get('volume')),
                    row.get('Adj Close', row.get('adj_close', row.get('close'))),
                    created_at
                ))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get cached fundamental data
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with fundamental data or None if not in cache/expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data, created_at
                FROM fundamental_data
                WHERE ticker = ?
            ''', (ticker,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Check if data is expired
            created_at = datetime.fromisoformat(result[1])
            if datetime.now() - created_at > timedelta(days=CACHE_EXPIRY_DAYS):
                return None
            
            return json.loads(result[0])
        finally:
            conn.close()
    
    def save_fundamental_data(self, ticker: str, data: Dict[str, Any]):
        """
        Save fundamental data to cache
        
        Args:
            ticker: Stock ticker symbol
            data: Dictionary with fundamental data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            created_at = datetime.now().isoformat()
            data_json = json.dumps(data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO fundamental_data (ticker, data, created_at)
                VALUES (?, ?, ?)
            ''', (ticker, data_json, created_at))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get cached stock info
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with stock info or None if not in cache/expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT info, created_at
                FROM stock_info
                WHERE ticker = ?
            ''', (ticker,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Check if data is expired
            created_at = datetime.fromisoformat(result[1])
            if datetime.now() - created_at > timedelta(days=CACHE_EXPIRY_DAYS):
                return None
            
            return json.loads(result[0])
        finally:
            conn.close()
    
    def save_stock_info(self, ticker: str, info: Dict[str, Any]):
        """
        Save stock info to cache
        
        Args:
            ticker: Stock ticker symbol
            info: Dictionary with stock info
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            created_at = datetime.now().isoformat()
            info_json = json.dumps(info)
            
            cursor.execute('''
                INSERT OR REPLACE INTO stock_info (ticker, info, created_at)
                VALUES (?, ?, ?)
            ''', (ticker, info_json, created_at))
            
            conn.commit()
        finally:
            conn.close()
    
    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear cache for a specific ticker or all tickers
        
        Args:
            ticker: Stock ticker symbol (None to clear all)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if ticker:
                cursor.execute('DELETE FROM historical_prices WHERE ticker = ?', (ticker,))
                cursor.execute('DELETE FROM fundamental_data WHERE ticker = ?', (ticker,))
                cursor.execute('DELETE FROM stock_info WHERE ticker = ?', (ticker,))
            else:
                cursor.execute('DELETE FROM historical_prices')
                cursor.execute('DELETE FROM fundamental_data')
                cursor.execute('DELETE FROM stock_info')
            
            conn.commit()
        finally:
            conn.close()
