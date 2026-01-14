# Stockies - Quick Start Guide

## Installation

### Prerequisites

- Python 3.12 or higher

### 1. Install UV (if not already installed)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or with pip:**
```bash
pip install uv
```

### 2. Set up Project

```bash
# Clone or navigate to project directory
cd stockies

# Install dependencies (creates venv automatically)
uv sync
```

That's it! UV automatically:
- Creates a virtual environment in `.venv`
- Installs all dependencies
- Locks dependency versions in `uv.lock`

### 3. Run the Application

```bash
# Run directly with UV (recommended)
uv run streamlit run app.py

# Or activate virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Quick Workflow

### Step 1: Scan for Stocks (Stock Scanner Page)

1. Choose input method:
   - **Predefined Universe**: Select from S&P 500, Tech, Healthcare, or Financial stocks
   - **Manual Entry**: Enter tickers like "AAPL, MSFT, GOOGL"
   - **Upload CSV**: Upload a CSV file with ticker symbols

2. Configure moat criteria:
   - Set minimum moat score (0-100)
   - Adjust fundamental and technical score thresholds
   - Higher scores indicate stronger economic moats

3. Click "🔍 Scan Stocks" to run the analysis

4. Review results:
   - Stocks are ranked by moat score
   - View detailed fundamental and technical metrics
   - Save to watchlist or download CSV

### Step 2: Build Strategy (Strategy Builder Page)

1. Create a new strategy or load an example:
   - Click "➕ New Strategy" for a blank template
   - Or select "RSI Mean Reversion" or "Momentum Breakout" examples

2. Define entry rules:
   ```
   Example: rsi(14) < 30 AND price > sma(200)
   ```
   This buys when RSI is oversold but price is above 200-day MA

3. Define exit rules:
   ```
   Example: rsi(14) > 70 OR price < entry_price * 0.95
   ```
   This sells when RSI is overbought or hits 5% stop loss

4. Configure position sizing:
   - **Percentage of Capital**: Allocate X% of capital per trade
   - **Fixed Amount**: Use fixed dollar amount per trade
   - **Risk-Based**: Size based on ATR and risk percentage

5. Set risk management:
   - Stop Loss: Automatic exit if price drops X%
   - Take Profit: Automatic exit if price rises X%
   - Trailing Stop: Lock in profits as price moves up

6. Click "💾 Save Strategy"

### Step 3: Run Backtest (Backtest Page)

1. Select stocks:
   - Choose from scanner results (if you ran scanner first)
   - Or manually enter a ticker

2. Select strategy:
   - Choose from saved strategies
   - The current strategy from Strategy Builder is pre-selected

3. Configure backtest:
   - Set date range (e.g., last 1 year)
   - Set initial capital (default: $100,000)
   - Adjust commission and slippage if needed

4. Click "🚀 Run Backtest"

5. Review results:
   - **Performance Summary**: Total return, CAGR, Sharpe ratio, max drawdown
   - **Equity Curve**: Visual representation of portfolio value over time
   - **Drawdown Chart**: See periods of losses
   - **Trade Analysis**: Individual trade details, P&L distribution, win/loss ratio
   - Download trade history as CSV

## Example Strategies Included

### 1. RSI Mean Reversion
- **Entry**: Buy when RSI < 30 and price > 200-day MA
- **Exit**: Sell when RSI > 70
- **Best for**: Range-bound markets, oversold bounces

### 2. Momentum Breakout
- **Entry**: Buy when price > 50-day MA with high volume and RSI > 50
- **Exit**: Sell when price < 20-day MA or RSI < 40
- **Best for**: Trending markets, breakout trades

## Tips for Best Results

### Stock Scanning
- Use moat score > 60 for high-quality stocks
- Combine fundamental (> 50) and technical (> 40) for balanced selection
- Tech stocks often score higher on fundamentals
- Financial stocks may have lower technical scores but strong fundamentals

### Strategy Building
- Start simple: Test basic RSI or MA crossover strategies first
- Add complexity gradually: Combine multiple indicators with AND/OR
- Use stop losses: Protect capital with 5-10% stop losses
- Test different timeframes: What works in bull markets may not work in bear markets

### Backtesting
- Use at least 1 year of data for meaningful results
- Compare multiple strategies on the same stocks
- Look for:
  - Sharpe ratio > 1.0 (good risk-adjusted returns)
  - Win rate > 50% (more winners than losers)
  - Profit factor > 1.5 (winners are bigger than losers)
  - Max drawdown < 20% (manageable losses)

## Troubleshooting

### "No data available for ticker"
- Check ticker symbol is correct (use Yahoo Finance format)
- Some stocks may not have sufficient historical data
- Try a different date range

### "Invalid entry/exit rules"
- Check syntax: Use correct indicator names and parameters
- Ensure logical operators are uppercase: AND, OR, NOT
- Use parentheses for indicator parameters: rsi(14), sma(200)

### Slow scanning
- Scanning many stocks takes time (Yahoo Finance API limits)
- Results are cached for 1 day to speed up subsequent scans
- Start with smaller universes (10-20 stocks) for testing

## Advanced Features

### Custom Indicators
Available indicators:
- Moving Averages: `sma(period)`, `ema(period)`, `wma(period)`
- Oscillators: `rsi(period)`, `stoch_k()`, `stoch_d()`, `williams_r()`
- Trend: `macd()`, `macd_signal()`, `macd_hist()`, `adx()`
- Volatility: `bb_upper()`, `bb_lower()`, `atr(period)`
- Volume: `obv()`, `vwap()`

### Complex Rules
Combine multiple conditions:
```
rsi(14) < 30 AND price > sma(200) AND volume > sma(volume, 20) * 1.5
```

Use OR for alternative conditions:
```
rsi(14) > 70 OR price < entry_price * 0.95 OR macd() < macd_signal()
```

### Multi-Stock Backtesting
Select multiple stocks in the backtest page to test portfolio-level performance.

## Next Steps

1. **Experiment**: Try different strategies on various stocks
2. **Optimize**: Adjust parameters (RSI periods, MA lengths, stop losses)
3. **Compare**: Run multiple backtests to find best strategies
4. **Document**: Keep notes on what works and what doesn't

## Important Disclaimer

This software is for educational and research purposes only. Past performance does not guarantee future results. Always do your own research and consult with a qualified financial advisor before making investment decisions.

## Support

For issues or questions, check the README.md file or review the code documentation.

Happy Trading! 📈
