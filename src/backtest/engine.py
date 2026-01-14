"""
Core backtesting engine
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from .portfolio import Portfolio, Trade
from .metrics import PerformanceMetrics
from src.strategy.rules_engine import RulesEngine
from src.data.fetcher import DataFetcher
from config.settings import DEFAULT_INITIAL_CAPITAL, DEFAULT_COMMISSION_RATE


class BacktestEngine:
    """Main backtesting engine for strategy evaluation"""
    
    def __init__(
        self,
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
        commission_rate: float = DEFAULT_COMMISSION_RATE,
        slippage_rate: float = 0
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        self.rules_engine = RulesEngine()
        self.data_fetcher = DataFetcher()
    
    def run_backtest(
        self,
        ticker: str,
        strategy: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Run backtest for a single stock
        
        Args:
            ticker: Stock ticker symbol
            strategy: Strategy dictionary
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with backtest results
        """
        # Fetch historical data
        df = self.data_fetcher.get_historical_data(ticker, start_date, end_date)
        
        if df.empty:
            return {
                'error': f'No data available for {ticker}',
                'ticker': ticker
            }
        
        # Apply strategy to generate signals
        df = self.rules_engine.apply_strategy(df, strategy)
        
        # Initialize portfolio
        portfolio = Portfolio(self.initial_capital, self.commission_rate)
        
        # Track entry price for exit rules
        entry_price = None
        in_position = False
        
        # Simulate trading
        for i in range(len(df)):
            date = df.index[i]
            row = df.iloc[i]
            
            current_price = row['Close']
            
            # Apply slippage
            buy_price = current_price * (1 + self.slippage_rate)
            sell_price = current_price * (1 - self.slippage_rate)
            
            # Check if we have an open position
            if in_position and ticker in portfolio.positions:
                # Update trailing stop
                if strategy.get('risk_management', {}).get('trailing_stop'):
                    portfolio.update_trailing_stop(ticker, current_price)
                
                # Check stop loss / take profit
                exit_reason = portfolio.check_exit_conditions(ticker, current_price, row['Low'])
                
                # Check exit signal from strategy
                exit_signal = row.get('exit_signal', False)
                
                if exit_reason or exit_signal:
                    # Close position
                    trade = portfolio.close_position(ticker, date, sell_price)
                    in_position = False
                    entry_price = None
            
            # Check entry signal
            elif not in_position and row.get('entry_signal', False):
                # Calculate position size
                atr = row.get('ATR_14', None)
                shares = self.rules_engine.get_position_size(
                    strategy,
                    portfolio.cash,
                    buy_price,
                    atr
                )
                
                if shares > 0:
                    # Calculate stop loss and take profit
                    risk_mgmt = strategy.get('risk_management', {})
                    
                    stop_loss = None
                    if 'stop_loss_pct' in risk_mgmt:
                        stop_loss = buy_price * (1 - risk_mgmt['stop_loss_pct'] / 100)
                    
                    take_profit = None
                    if 'take_profit_pct' in risk_mgmt:
                        take_profit = buy_price * (1 + risk_mgmt['take_profit_pct'] / 100)
                    
                    trailing_stop = risk_mgmt.get('trailing_stop_pct', None) if risk_mgmt.get('trailing_stop') else None
                    
                    # Open position
                    success = portfolio.open_position(
                        ticker,
                        date,
                        buy_price,
                        shares,
                        stop_loss,
                        take_profit,
                        trailing_stop
                    )
                    
                    if success:
                        in_position = True
                        entry_price = buy_price
            
            # Record equity
            current_prices = {ticker: current_price}
            portfolio.record_equity(date, current_prices)
        
        # Close any remaining positions at the end
        if ticker in portfolio.positions:
            last_price = df['Close'].iloc[-1] * (1 - self.slippage_rate)
            portfolio.close_position(ticker, df.index[-1], last_price)
        
        # Calculate performance metrics
        equity_df = pd.DataFrame(portfolio.equity_curve)
        metrics = PerformanceMetrics.calculate_all_metrics(
            equity_df,
            portfolio.trades,
            self.initial_capital
        )
        
        # Prepare results
        results = {
            'ticker': ticker,
            'strategy_name': strategy.get('name', 'Unknown'),
            'start_date': start_date,
            'end_date': end_date,
            'metrics': metrics,
            'trades': portfolio.trades,
            'equity_curve': equity_df,
            'portfolio_stats': portfolio.get_statistics()
        }
        
        return results
    
    def run_multi_stock_backtest(
        self,
        tickers: List[str],
        strategy: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Run backtest across multiple stocks (portfolio approach)
        
        Args:
            tickers: List of stock ticker symbols
            strategy: Strategy dictionary
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with combined backtest results
        """
        # Initialize portfolio
        portfolio = Portfolio(self.initial_capital, self.commission_rate)
        
        # Fetch data for all stocks
        stock_data = {}
        for ticker in tickers:
            df = self.data_fetcher.get_historical_data(ticker, start_date, end_date)
            if not df.empty:
                df = self.rules_engine.apply_strategy(df, strategy)
                stock_data[ticker] = df
        
        if not stock_data:
            return {'error': 'No data available for any tickers'}
        
        # Get all unique dates
        all_dates = sorted(set().union(*[set(df.index) for df in stock_data.values()]))
        
        # Track positions
        in_position = {}
        entry_prices = {}
        
        # Simulate trading day by day
        for date in all_dates:
            current_prices = {}
            
            # Process each stock
            for ticker, df in stock_data.items():
                if date not in df.index:
                    continue
                
                row = df.loc[date]
                current_price = row['Close']
                current_prices[ticker] = current_price
                
                # Apply slippage
                buy_price = current_price * (1 + self.slippage_rate)
                sell_price = current_price * (1 - self.slippage_rate)
                
                # Check existing position
                if ticker in portfolio.positions:
                    # Update trailing stop
                    if strategy.get('risk_management', {}).get('trailing_stop'):
                        portfolio.update_trailing_stop(ticker, current_price)
                    
                    # Check exit conditions
                    exit_reason = portfolio.check_exit_conditions(ticker, current_price, row['Low'])
                    exit_signal = row.get('exit_signal', False)
                    
                    if exit_reason or exit_signal:
                        portfolio.close_position(ticker, date, sell_price)
                        in_position[ticker] = False
                
                # Check entry signal
                elif row.get('entry_signal', False):
                    # Calculate position size (divide capital among stocks)
                    atr = row.get('ATR_14', None)
                    shares = self.rules_engine.get_position_size(
                        strategy,
                        portfolio.cash,
                        buy_price,
                        atr
                    )
                    
                    if shares > 0:
                        risk_mgmt = strategy.get('risk_management', {})
                        
                        stop_loss = None
                        if 'stop_loss_pct' in risk_mgmt:
                            stop_loss = buy_price * (1 - risk_mgmt['stop_loss_pct'] / 100)
                        
                        take_profit = None
                        if 'take_profit_pct' in risk_mgmt:
                            take_profit = buy_price * (1 + risk_mgmt['take_profit_pct'] / 100)
                        
                        trailing_stop = risk_mgmt.get('trailing_stop_pct', None) if risk_mgmt.get('trailing_stop') else None
                        
                        success = portfolio.open_position(
                            ticker,
                            date,
                            buy_price,
                            shares,
                            stop_loss,
                            take_profit,
                            trailing_stop
                        )
                        
                        if success:
                            in_position[ticker] = True
                            entry_prices[ticker] = buy_price
            
            # Record equity
            portfolio.record_equity(date, current_prices)
        
        # Close remaining positions
        for ticker in list(portfolio.positions.keys()):
            if ticker in stock_data:
                last_price = stock_data[ticker]['Close'].iloc[-1] * (1 - self.slippage_rate)
                portfolio.close_position(ticker, stock_data[ticker].index[-1], last_price)
        
        # Calculate metrics
        equity_df = pd.DataFrame(portfolio.equity_curve)
        metrics = PerformanceMetrics.calculate_all_metrics(
            equity_df,
            portfolio.trades,
            self.initial_capital
        )
        
        return {
            'tickers': tickers,
            'strategy_name': strategy.get('name', 'Unknown'),
            'start_date': start_date,
            'end_date': end_date,
            'metrics': metrics,
            'trades': portfolio.trades,
            'equity_curve': equity_df,
            'portfolio_stats': portfolio.get_statistics()
        }
