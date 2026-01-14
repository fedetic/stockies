"""
Stock screener interface
"""
import pandas as pd
from typing import List, Optional, Dict, Any

from .moat_analyzer import MoatAnalyzer
from src.data.fetcher import DataFetcher


class StockScreener:
    """Stock screening with moat analysis"""
    
    # Popular indices
    SP500_SAMPLE = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'UNH', 'JNJ',
        'V', 'XOM', 'WMT', 'JPM', 'PG', 'MA', 'HD', 'CVX', 'LLY', 'ABBV',
        'MRK', 'KO', 'PEP', 'AVGO', 'COST', 'TMO', 'MCD', 'ADBE', 'CSCO', 'ACN'
    ]
    
    TECH_STOCKS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'ADBE', 'CRM', 'ORCL',
        'INTC', 'AMD', 'QCOM', 'IBM', 'SNOW', 'PLTR', 'UBER', 'SQ', 'SHOP', 'DOCU'
    ]
    
    HEALTHCARE_STOCKS = [
        'JNJ', 'UNH', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR', 'BMY',
        'AMGN', 'GILD', 'CVS', 'CI', 'MDT', 'ISRG', 'VRTX', 'REGN', 'HUM', 'ZTS'
    ]
    
    FINANCIAL_STOCKS = [
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'CB',
        'PNC', 'USB', 'TFC', 'COF', 'BK', 'AIG', 'MET', 'PRU', 'ALL', 'TRV'
    ]
    
    def __init__(self, moat_analyzer: Optional[MoatAnalyzer] = None):
        self.moat_analyzer = moat_analyzer or MoatAnalyzer()
        self.data_fetcher = DataFetcher()
    
    def screen_stocks(
        self,
        tickers: List[str],
        min_moat_score: float = 0,
        min_fundamental_score: float = 0,
        min_technical_score: float = 0
    ) -> pd.DataFrame:
        """
        Screen stocks based on moat criteria
        
        Args:
            tickers: List of stock ticker symbols
            min_moat_score: Minimum overall moat score (0-100)
            min_fundamental_score: Minimum fundamental score (0-100)
            min_technical_score: Minimum technical score (0-100)
            
        Returns:
            DataFrame with screening results
        """
        # Analyze all stocks
        results = self.moat_analyzer.batch_analyze(tickers)
        
        if results.empty:
            return results
        
        # Apply filters
        filtered = results[
            (results['moat_score'] >= min_moat_score) &
            (results['fundamental_score'] >= min_fundamental_score) &
            (results['technical_score'] >= min_technical_score)
        ]
        
        return filtered
    
    def screen_by_universe(
        self,
        universe: str = 'SP500',
        min_moat_score: float = 50,
        top_n: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Screen stocks from a predefined universe
        
        Args:
            universe: Stock universe ('SP500', 'TECH', 'HEALTHCARE', 'FINANCIAL')
            min_moat_score: Minimum overall moat score
            top_n: Return only top N stocks (None for all)
            
        Returns:
            DataFrame with screening results
        """
        # Get ticker list for universe
        universe_map = {
            'SP500': self.SP500_SAMPLE,
            'TECH': self.TECH_STOCKS,
            'HEALTHCARE': self.HEALTHCARE_STOCKS,
            'FINANCIAL': self.FINANCIAL_STOCKS
        }
        
        tickers = universe_map.get(universe.upper(), self.SP500_SAMPLE)
        
        # Screen stocks
        results = self.screen_stocks(tickers, min_moat_score=min_moat_score)
        
        # Return top N if specified
        if top_n and not results.empty:
            results = results.head(top_n)
        
        return results
    
    def get_stock_details(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific stock
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with detailed stock information
        """
        # Get moat analysis
        analysis = self.moat_analyzer.analyze_stock(ticker)
        
        # Get additional info
        info = self.data_fetcher.get_stock_info(ticker)
        
        # Get latest price
        latest_price = self.data_fetcher.get_latest_price(ticker)
        
        return {
            'ticker': ticker.upper(),
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'latest_price': latest_price,
            'market_cap': info.get('marketCap', None),
            'moat_analysis': analysis,
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'dividend_yield': info.get('dividendYield', None),
            'beta': info.get('beta', None)
        }
    
    @staticmethod
    def parse_ticker_input(input_text: str) -> List[str]:
        """
        Parse ticker input from various formats
        
        Args:
            input_text: Input text with tickers (comma/space/newline separated)
            
        Returns:
            List of ticker symbols
        """
        # Replace common separators with spaces
        text = input_text.replace(',', ' ').replace('\n', ' ').replace('\t', ' ')
        
        # Split and clean
        tickers = [t.strip().upper() for t in text.split() if t.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for ticker in tickers:
            if ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)
        
        return unique_tickers
