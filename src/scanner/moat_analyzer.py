"""
Moat analyzer - Combined fundamental and technical scoring
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from src.data.fetcher import DataFetcher
from src.strategy.indicators import Indicators
from config.settings import (
    MOAT_FUNDAMENTAL_WEIGHT,
    MOAT_TECHNICAL_WEIGHT,
    FUNDAMENTAL_THRESHOLDS,
    TECHNICAL_PARAMS
)


class MoatAnalyzer:
    """Analyzes stocks for economic moat using fundamental and technical criteria"""
    
    def __init__(self, data_fetcher: Optional[DataFetcher] = None):
        self.data_fetcher = data_fetcher or DataFetcher()
    
    def analyze_stock(self, ticker: str) -> Dict[str, Any]:
        """
        Analyze a stock for moat characteristics
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with moat analysis results
        """
        # Get fundamental score
        fundamental_score, fundamental_details = self._calculate_fundamental_score(ticker)
        
        # Get technical score
        technical_score, technical_details = self._calculate_technical_score(ticker)
        
        # Calculate overall moat score
        moat_score = (
            fundamental_score * MOAT_FUNDAMENTAL_WEIGHT +
            technical_score * MOAT_TECHNICAL_WEIGHT
        )
        
        return {
            'ticker': ticker.upper(),
            'moat_score': round(moat_score, 2),
            'fundamental_score': round(fundamental_score, 2),
            'technical_score': round(technical_score, 2),
            'fundamental_details': fundamental_details,
            'technical_details': technical_details,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_fundamental_score(self, ticker: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate fundamental moat score
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {
            'roe': None,
            'operating_margin': None,
            'debt_to_equity': None,
            'fcf_positive': None,
            'revenue_growth': None,
            'earnings_growth': None
        }
        
        try:
            # Get stock info
            info = self.data_fetcher.get_stock_info(ticker)
            
            # Get fundamental data
            fundamentals = self.data_fetcher.get_fundamental_data(ticker)
            
            # Extract metrics
            roe = info.get('returnOnEquity', None)
            operating_margin = info.get('operatingMargins', None)
            debt_to_equity = info.get('debtToEquity', None)
            
            # Calculate free cash flow
            fcf_positive = None
            if fundamentals['cash_flow']:
                try:
                    cash_flow_df = pd.DataFrame(fundamentals['cash_flow'])
                    if 'Free Cash Flow' in cash_flow_df.index and not cash_flow_df.empty:
                        latest_fcf = cash_flow_df.loc['Free Cash Flow'].iloc[0]
                        fcf_positive = latest_fcf > 0
                except Exception:
                    pass
            
            # Calculate revenue and earnings growth
            revenue_growth = info.get('revenueGrowth', None)
            earnings_growth = info.get('earningsGrowth', None)
            
            # Store details
            details['roe'] = roe
            details['operating_margin'] = operating_margin
            details['debt_to_equity'] = debt_to_equity / 100 if debt_to_equity else None  # Convert to ratio
            details['fcf_positive'] = fcf_positive
            details['revenue_growth'] = revenue_growth
            details['earnings_growth'] = earnings_growth
            
            # Calculate score
            score = 0
            max_score = 100
            
            # ROE score (25 points)
            if roe is not None:
                if roe >= FUNDAMENTAL_THRESHOLDS['roe']:
                    score += 25
                else:
                    score += 25 * (roe / FUNDAMENTAL_THRESHOLDS['roe'])
            
            # Operating margin score (25 points)
            if operating_margin is not None:
                if operating_margin >= FUNDAMENTAL_THRESHOLDS['operating_margin']:
                    score += 25
                else:
                    score += 25 * (operating_margin / FUNDAMENTAL_THRESHOLDS['operating_margin'])
            
            # Debt-to-equity score (20 points) - lower is better
            if debt_to_equity is not None:
                debt_ratio = debt_to_equity / 100  # Convert to ratio
                if debt_ratio <= FUNDAMENTAL_THRESHOLDS['debt_to_equity']:
                    score += 20
                else:
                    score += max(0, 20 * (1 - (debt_ratio - FUNDAMENTAL_THRESHOLDS['debt_to_equity'])))
            
            # Free cash flow score (15 points)
            if fcf_positive is not None:
                if fcf_positive:
                    score += 15
            
            # Revenue growth score (10 points)
            if revenue_growth is not None and revenue_growth > 0:
                score += min(10, 10 * (revenue_growth / 0.10))  # Max at 10% growth
            
            # Earnings growth score (5 points)
            if earnings_growth is not None and earnings_growth > 0:
                score += min(5, 5 * (earnings_growth / 0.10))  # Max at 10% growth
            
            return min(score, max_score), details
        
        except Exception as e:
            print(f"Error calculating fundamental score for {ticker}: {str(e)}")
            return 0, details
    
    def _calculate_technical_score(self, ticker: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate technical moat score
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {
            'above_ma_200': None,
            'price_trend': None,
            'volume_trend': None,
            'relative_strength': None,
            'support_strength': None
        }
        
        try:
            # Get historical data (1 year)
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            df = self.data_fetcher.get_historical_data(ticker, start_date, end_date)
            
            if df.empty:
                return 0, details
            
            # Calculate indicators
            df['SMA_200'] = Indicators.sma(df['Close'], TECHNICAL_PARAMS['ma_period'])
            df['SMA_50'] = Indicators.sma(df['Close'], 50)
            df['Volume_MA'] = Indicators.sma(df['Volume'], TECHNICAL_PARAMS['volume_ma_period'])
            
            # Get latest values
            latest = df.iloc[-1]
            
            score = 0
            max_score = 100
            
            # Price above 200-day MA (30 points)
            if not pd.isna(latest['SMA_200']):
                if latest['Close'] > latest['SMA_200']:
                    score += 30
                    details['above_ma_200'] = True
                else:
                    details['above_ma_200'] = False
            
            # Price trend - 50 vs 200 MA (25 points)
            if not pd.isna(latest['SMA_50']) and not pd.isna(latest['SMA_200']):
                if latest['SMA_50'] > latest['SMA_200']:
                    score += 25
                    details['price_trend'] = 'bullish'
                else:
                    details['price_trend'] = 'bearish'
            
            # Volume trend (20 points)
            if not pd.isna(latest['Volume_MA']):
                recent_volume_avg = df['Volume'].tail(5).mean()
                if recent_volume_avg > latest['Volume_MA']:
                    score += 20
                    details['volume_trend'] = 'increasing'
                else:
                    score += 10
                    details['volume_trend'] = 'normal'
            
            # Relative strength - compare to 3-month ago (15 points)
            if len(df) >= 63:  # ~3 months of trading days
                price_3m_ago = df['Close'].iloc[-63]
                price_return = (latest['Close'] - price_3m_ago) / price_3m_ago
                
                if price_return > 0.10:  # >10% gain
                    score += 15
                    details['relative_strength'] = 'strong'
                elif price_return > 0:
                    score += 7
                    details['relative_strength'] = 'positive'
                else:
                    details['relative_strength'] = 'weak'
            
            # Support level strength (10 points) - check if price bounced off MA
            if len(df) >= 20:
                recent_df = df.tail(20)
                touches = 0
                for i in range(len(recent_df) - 1):
                    if not pd.isna(recent_df['SMA_50'].iloc[i]):
                        # Check if price touched but didn't break MA
                        if (recent_df['Low'].iloc[i] <= recent_df['SMA_50'].iloc[i] <= recent_df['High'].iloc[i] and
                            recent_df['Close'].iloc[i] >= recent_df['SMA_50'].iloc[i]):
                            touches += 1
                
                if touches >= 2:
                    score += 10
                    details['support_strength'] = 'strong'
                elif touches >= 1:
                    score += 5
                    details['support_strength'] = 'moderate'
                else:
                    details['support_strength'] = 'weak'
            
            return min(score, max_score), details
        
        except Exception as e:
            print(f"Error calculating technical score for {ticker}: {str(e)}")
            return 0, details
    
    def batch_analyze(self, tickers: list) -> pd.DataFrame:
        """
        Analyze multiple stocks
        
        Args:
            tickers: List of stock ticker symbols
            
        Returns:
            DataFrame with analysis results sorted by moat_score
        """
        results = []
        
        for ticker in tickers:
            try:
                analysis = self.analyze_stock(ticker)
                results.append(analysis)
            except Exception as e:
                print(f"Error analyzing {ticker}: {str(e)}")
                continue
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        df = df.sort_values('moat_score', ascending=False)
        
        return df
