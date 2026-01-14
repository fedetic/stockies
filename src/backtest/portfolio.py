"""
Portfolio management for backtesting
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Position:
    """Represents a stock position"""
    ticker: str
    entry_date: datetime
    entry_price: float
    quantity: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    
    @property
    def cost_basis(self) -> float:
        """Total cost of the position"""
        return self.entry_price * self.quantity
    
    def current_value(self, current_price: float) -> float:
        """Current value of the position"""
        return current_price * self.quantity
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Unrealized profit/loss"""
        return (current_price - self.entry_price) * self.quantity
    
    def unrealized_pnl_pct(self, current_price: float) -> float:
        """Unrealized profit/loss percentage"""
        return ((current_price - self.entry_price) / self.entry_price) * 100


@dataclass
class Trade:
    """Represents a completed trade"""
    ticker: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: int
    commission: float = 0
    
    @property
    def pnl(self) -> float:
        """Profit/loss including commission"""
        gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        return gross_pnl - self.commission
    
    @property
    def pnl_pct(self) -> float:
        """Profit/loss percentage"""
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def holding_days(self) -> int:
        """Number of days position was held"""
        return (self.exit_date - self.entry_date).days


class Portfolio:
    """Manages portfolio state during backtesting"""
    
    def __init__(self, initial_capital: float, commission_rate: float = 0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
        self.total_commission = 0
    
    @property
    def total_position_value(self) -> float:
        """Total value of all open positions at current prices"""
        return sum(pos.cost_basis for pos in self.positions.values())
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        Get total portfolio value (cash + positions)
        
        Args:
            current_prices: Dictionary mapping ticker to current price
            
        Returns:
            Total portfolio value
        """
        position_value = sum(
            pos.current_value(current_prices.get(ticker, pos.entry_price))
            for ticker, pos in self.positions.items()
        )
        return self.cash + position_value
    
    def open_position(
        self,
        ticker: str,
        date: datetime,
        price: float,
        quantity: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: Optional[float] = None
    ) -> bool:
        """
        Open a new position
        
        Args:
            ticker: Stock ticker
            date: Entry date
            price: Entry price
            quantity: Number of shares
            stop_loss: Stop loss price
            take_profit: Take profit price
            trailing_stop: Trailing stop percentage
            
        Returns:
            True if position opened successfully, False otherwise
        """
        if quantity <= 0:
            return False
        
        cost = price * quantity
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        # Check if we have enough cash
        if total_cost > self.cash:
            return False
        
        # Create position
        position = Position(
            ticker=ticker,
            entry_date=date,
            entry_price=price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop
        )
        
        # Update portfolio
        self.positions[ticker] = position
        self.cash -= total_cost
        self.total_commission += commission
        
        return True
    
    def close_position(
        self,
        ticker: str,
        date: datetime,
        price: float
    ) -> Optional[Trade]:
        """
        Close an existing position
        
        Args:
            ticker: Stock ticker
            date: Exit date
            price: Exit price
            
        Returns:
            Trade object if position closed, None otherwise
        """
        if ticker not in self.positions:
            return None
        
        position = self.positions[ticker]
        
        proceeds = price * position.quantity
        commission = proceeds * self.commission_rate
        net_proceeds = proceeds - commission
        
        # Create trade record
        trade = Trade(
            ticker=ticker,
            entry_date=position.entry_date,
            exit_date=date,
            entry_price=position.entry_price,
            exit_price=price,
            quantity=position.quantity,
            commission=self.total_commission
        )
        
        # Update portfolio
        self.cash += net_proceeds
        self.total_commission += commission
        self.trades.append(trade)
        del self.positions[ticker]
        
        return trade
    
    def update_trailing_stop(self, ticker: str, current_price: float):
        """
        Update trailing stop for a position
        
        Args:
            ticker: Stock ticker
            current_price: Current price
        """
        if ticker not in self.positions:
            return
        
        position = self.positions[ticker]
        
        if position.trailing_stop:
            # Calculate new trailing stop
            stop_price = current_price * (1 - position.trailing_stop / 100)
            
            # Update if higher than current stop loss
            if position.stop_loss is None or stop_price > position.stop_loss:
                position.stop_loss = stop_price
    
    def check_exit_conditions(
        self,
        ticker: str,
        current_price: float,
        low_price: float
    ) -> Optional[str]:
        """
        Check if position should be closed based on stop loss/take profit
        
        Args:
            ticker: Stock ticker
            current_price: Current close price
            low_price: Low price for the period
            
        Returns:
            Reason for exit ('stop_loss', 'take_profit', or None)
        """
        if ticker not in self.positions:
            return None
        
        position = self.positions[ticker]
        
        # Check stop loss (use low price)
        if position.stop_loss and low_price <= position.stop_loss:
            return 'stop_loss'
        
        # Check take profit (use close price)
        if position.take_profit and current_price >= position.take_profit:
            return 'take_profit'
        
        return None
    
    def record_equity(self, date: datetime, current_prices: Dict[str, float]):
        """
        Record current portfolio equity
        
        Args:
            date: Current date
            current_prices: Dictionary mapping ticker to current price
        """
        total_value = self.get_total_value(current_prices)
        
        self.equity_curve.append({
            'date': date,
            'equity': total_value,
            'cash': self.cash,
            'positions_value': total_value - self.cash
        })
    
    def get_statistics(self) -> Dict:
        """
        Get portfolio statistics
        
        Returns:
            Dictionary with portfolio statistics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_commission': self.total_commission
            }
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100 if self.trades else 0,
            'total_pnl': sum(t.pnl for t in self.trades),
            'avg_win': sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_loss': sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            'total_commission': self.total_commission,
            'avg_holding_days': sum(t.holding_days for t in self.trades) / len(self.trades) if self.trades else 0
        }
