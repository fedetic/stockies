"""
Performance metrics calculations
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from scipy import stats


class PerformanceMetrics:
    """Calculate trading performance metrics"""
    
    @staticmethod
    def calculate_returns(equity_curve: pd.DataFrame) -> pd.Series:
        """
        Calculate period returns
        
        Args:
            equity_curve: DataFrame with date and equity columns
            
        Returns:
            Series with period returns
        """
        return equity_curve['equity'].pct_change().fillna(0)
    
    @staticmethod
    def total_return(initial_capital: float, final_equity: float) -> float:
        """
        Calculate total return percentage
        
        Args:
            initial_capital: Starting capital
            final_equity: Ending equity
            
        Returns:
            Total return percentage
        """
        return ((final_equity - initial_capital) / initial_capital) * 100
    
    @staticmethod
    def cagr(initial_capital: float, final_equity: float, years: float) -> float:
        """
        Calculate Compound Annual Growth Rate
        
        Args:
            initial_capital: Starting capital
            final_equity: Ending equity
            years: Number of years
            
        Returns:
            CAGR percentage
        """
        if years <= 0 or initial_capital <= 0:
            return 0
        
        return (((final_equity / initial_capital) ** (1 / years)) - 1) * 100
    
    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio
        
        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        if returns.std() == 0:
            return 0
        
        # Convert annual risk-free rate to period rate
        period_rf = risk_free_rate / 252  # Assuming daily returns
        
        excess_returns = returns - period_rf
        return np.sqrt(252) * (excess_returns.mean() / returns.std())
    
    @staticmethod
    def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino Ratio (uses downside deviation)
        
        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sortino ratio
        """
        period_rf = risk_free_rate / 252
        excess_returns = returns - period_rf
        
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        
        downside_std = downside_returns.std()
        return np.sqrt(252) * (excess_returns.mean() / downside_std)
    
    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> Dict[str, float]:
        """
        Calculate maximum drawdown
        
        Args:
            equity_curve: Series with equity values
            
        Returns:
            Dictionary with max_drawdown, peak, trough
        """
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax * 100
        
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Find the peak before the max drawdown
        peak_idx = equity_curve[:max_dd_idx].idxmax() if max_dd_idx else 0
        
        return {
            'max_drawdown_pct': max_dd,
            'peak_date': peak_idx,
            'trough_date': max_dd_idx,
            'peak_value': equity_curve[peak_idx] if peak_idx else 0,
            'trough_value': equity_curve[max_dd_idx] if max_dd_idx else 0
        }
    
    @staticmethod
    def win_rate(trades: List[Any]) -> float:
        """
        Calculate win rate
        
        Args:
            trades: List of Trade objects
            
        Returns:
            Win rate percentage
        """
        if not trades:
            return 0
        
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        return (winning_trades / len(trades)) * 100
    
    @staticmethod
    def profit_factor(trades: List[Any]) -> float:
        """
        Calculate profit factor (gross profit / gross loss)
        
        Args:
            trades: List of Trade objects
            
        Returns:
            Profit factor
        """
        if not trades:
            return 0
        
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0
        
        return gross_profit / gross_loss
    
    @staticmethod
    def expectancy(trades: List[Any]) -> float:
        """
        Calculate expectancy (average trade profit)
        
        Args:
            trades: List of Trade objects
            
        Returns:
            Expectancy value
        """
        if not trades:
            return 0
        
        return sum(t.pnl for t in trades) / len(trades)
    
    @staticmethod
    def calculate_all_metrics(
        equity_curve: pd.DataFrame,
        trades: List[Any],
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Calculate all performance metrics
        
        Args:
            equity_curve: DataFrame with date and equity columns
            trades: List of Trade objects
            initial_capital: Starting capital
            
        Returns:
            Dictionary with all metrics
        """
        if equity_curve.empty:
            return {}
        
        final_equity = equity_curve['equity'].iloc[-1]
        returns = PerformanceMetrics.calculate_returns(equity_curve)
        
        # Calculate time period in years
        days = (equity_curve['date'].iloc[-1] - equity_curve['date'].iloc[0]).days
        years = days / 365.25
        
        # Basic metrics
        metrics = {
            'initial_capital': initial_capital,
            'final_equity': final_equity,
            'total_return_pct': PerformanceMetrics.total_return(initial_capital, final_equity),
            'cagr_pct': PerformanceMetrics.cagr(initial_capital, final_equity, years),
        }
        
        # Risk-adjusted metrics
        if len(returns) > 1:
            metrics.update({
                'sharpe_ratio': PerformanceMetrics.sharpe_ratio(returns),
                'sortino_ratio': PerformanceMetrics.sortino_ratio(returns),
            })
        
        # Drawdown metrics
        dd_metrics = PerformanceMetrics.max_drawdown(equity_curve['equity'])
        metrics.update(dd_metrics)
        
        # Trade metrics
        if trades:
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            
            metrics.update({
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate_pct': PerformanceMetrics.win_rate(trades),
                'profit_factor': PerformanceMetrics.profit_factor(trades),
                'expectancy': PerformanceMetrics.expectancy(trades),
                'avg_win': sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                'avg_loss': sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                'largest_win': max((t.pnl for t in trades), default=0),
                'largest_loss': min((t.pnl for t in trades), default=0),
                'avg_holding_days': sum(t.holding_days for t in trades) / len(trades),
            })
        
        return metrics
    
    @staticmethod
    def get_monthly_returns(equity_curve: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate monthly returns
        
        Args:
            equity_curve: DataFrame with date and equity columns
            
        Returns:
            DataFrame with monthly returns
        """
        df = equity_curve.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # Resample to monthly and calculate returns
        monthly = df['equity'].resample('M').last()
        monthly_returns = monthly.pct_change() * 100
        
        return monthly_returns.to_frame(name='return_pct')
    
    @staticmethod
    def get_trade_distribution(trades: List[Any]) -> Dict[str, Any]:
        """
        Get distribution statistics for trades
        
        Args:
            trades: List of Trade objects
            
        Returns:
            Dictionary with distribution statistics
        """
        if not trades:
            return {}
        
        pnls = [t.pnl for t in trades]
        pnl_pcts = [t.pnl_pct for t in trades]
        
        return {
            'mean_pnl': np.mean(pnls),
            'median_pnl': np.median(pnls),
            'std_pnl': np.std(pnls),
            'mean_pnl_pct': np.mean(pnl_pcts),
            'median_pnl_pct': np.median(pnl_pcts),
            'std_pnl_pct': np.std(pnl_pcts),
        }
