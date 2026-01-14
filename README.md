# Stockies - Swing Trading Backtest Application

A powerful web-based application for swing traders to scan stocks with economic moats, configure custom trading strategies, and instantly visualize backtest P&L results.

## Features

- **Stock Scanner with Moat Analysis**: Identify stocks with strong competitive advantages using combined fundamental and technical scoring
- **Advanced Strategy Builder**: Create custom trading strategies with complex rules, indicators, and risk management
- **Instant Backtesting**: Run backtests and see P&L results immediately with detailed performance metrics
- **Interactive Visualizations**: Equity curves, drawdown charts, trade analysis, and more
- **Data Caching**: Efficient SQLite caching to minimize API calls and speed up analysis

## Installation

### Prerequisites

- Python 3.12 or higher
- UV package manager (from Astral)

### Install UV

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or with pip:
```bash
pip install uv
```

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd stockies
```

2. Create virtual environment and install dependencies (UV does this automatically):
```bash
uv sync
```

That's it! UV will create a virtual environment, install all dependencies, and lock versions.

## Usage

Run the application:
```bash
uv run streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Alternative: Activate virtual environment

If you prefer to activate the virtual environment:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
streamlit run app.py
```

## Application Workflow

1. **Stock Scanner**: 
   - Select stocks to scan (manual entry, upload CSV, or use predefined indices)
   - Configure moat scoring criteria (fundamental and technical weights)
   - View ranked results with detailed scores
   - Export to watchlist

2. **Strategy Builder**:
   - Create entry and exit rules using visual rule builder or text editor
   - Configure position sizing and risk management parameters
   - Save strategies for reuse
   - Load example strategies to get started

3. **Backtest**:
   - Select stocks from scanner or manually
   - Choose a strategy
   - Set date range and capital
   - Run backtest and view instant results:
     - Total return, CAGR, Sharpe ratio, maximum drawdown
     - Equity curve and drawdown visualization
     - Individual trade details
     - Performance statistics

## Project Structure

```
stockies/
├── app.py                      # Main Streamlit application
├── pyproject.toml              # Project metadata and dependencies (UV)
├── uv.lock                     # Locked dependency versions (UV)
├── .python-version             # Python version for UV
├── config/
│   └── settings.py            # Configuration settings
├── src/
│   ├── data/                  # Data fetching and caching
│   ├── scanner/               # Stock screening and moat analysis
│   ├── strategy/              # Strategy rules engine and indicators
│   ├── backtest/              # Backtesting engine and metrics
│   ├── ui/                    # Streamlit UI pages
│   └── utils/                 # Validation and utilities
├── data/                      # SQLite cache (auto-generated)
└── strategies/                # Saved strategy JSON files
```

## Configuration

Edit `config/settings.py` to customize:
- Initial capital and commission rates
- Moat scoring weights and thresholds
- Cache settings
- Technical indicator parameters

## Technology Stack

- **Package Manager**: UV (Astral)
- **Frontend**: Streamlit
- **Data Source**: Yahoo Finance (via yfinance)
- **Data Processing**: pandas, numpy
- **Technical Analysis**: pandas-ta
- **Visualization**: plotly
- **Database**: SQLite with SQLAlchemy

## Adding Dependencies

Add new packages with UV:
```bash
uv add <package-name>
```

For development dependencies:
```bash
uv add --dev <package-name>
```

Update dependencies:
```bash
uv sync --upgrade
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Disclaimer

This software is for educational and research purposes only. It is not financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.
