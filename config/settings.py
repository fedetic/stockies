"""
Application configuration settings
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STRATEGIES_DIR = PROJECT_ROOT / "strategies"
CACHE_DB_PATH = DATA_DIR / "cache.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
STRATEGIES_DIR.mkdir(exist_ok=True)
(STRATEGIES_DIR / "examples").mkdir(exist_ok=True)

# Cache settings
CACHE_EXPIRY_DAYS = 1  # Expire cached data after 1 day
MAX_CACHE_SIZE_MB = 500  # Maximum cache size in MB

# Trading settings
DEFAULT_INITIAL_CAPITAL = 100000.0  # $100,000
DEFAULT_COMMISSION_RATE = 0.001  # 0.1% per trade
DEFAULT_SLIPPAGE_RATE = 0.0005  # 0.05% slippage

# Moat scoring weights
MOAT_FUNDAMENTAL_WEIGHT = 0.6
MOAT_TECHNICAL_WEIGHT = 0.4

# Fundamental criteria thresholds
FUNDAMENTAL_THRESHOLDS = {
    'roe': 0.15,  # 15% ROE
    'operating_margin': 0.20,  # 20% operating margin
    'debt_to_equity': 0.5,  # Max 0.5 D/E ratio
    'fcf_positive': True,  # Must have positive free cash flow
}

# Technical criteria
TECHNICAL_PARAMS = {
    'ma_period': 200,  # 200-day moving average
    'volume_ma_period': 20,  # 20-day volume moving average
}

# Data fetching
YAHOO_FINANCE_TIMEOUT = 30  # seconds
DEFAULT_TIMEFRAME = '1d'
