"""
Main Streamlit application for Stockies - Swing Trading Backtest App
"""
import streamlit as st

from src.ui.scanner_page import render_scanner_page
from src.ui.strategy_page import render_strategy_page
from src.ui.backtest_page import render_backtest_page


# Page configuration
st.set_page_config(
    page_title="Stockies - Swing Trading Backtest",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
    }
    h1 {
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.title("📊 Stockies")
    st.markdown("**Swing Trading Backtest App**")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Home", "🔍 Stock Scanner", "⚙️ Strategy Builder", "📈 Backtest"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### Quick Stats")
    
    if 'watchlist' in st.session_state:
        st.metric("Watchlist", len(st.session_state.watchlist))
    else:
        st.metric("Watchlist", 0)
    
    if 'backtest_results' in st.session_state:
        results = st.session_state.backtest_results
        if 'metrics' in results:
            total_return = results['metrics'].get('total_return_pct', 0)
            st.metric("Last Backtest Return", f"{total_return:.2f}%")
    
    st.markdown("---")
    
    # Info
    st.markdown("### About")
    st.markdown("""
    Stockies helps swing traders:
    - Scan stocks with economic moats
    - Build custom trading strategies
    - Backtest and analyze P&L instantly
    """)
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")


# Main content area
if page == "🏠 Home":
    st.title("Welcome to Stockies 📊")
    st.markdown("### Your Swing Trading Backtest Platform")
    
    st.markdown("""
    Stockies is a powerful web application designed for swing traders to:
    
    1. **📊 Scan Stocks**: Find stocks with strong economic moats using fundamental and technical analysis
    2. **⚙️ Build Strategies**: Create custom trading strategies with advanced rules and risk management
    3. **📈 Backtest**: Run backtests instantly and visualize P&L results with detailed metrics
    
    ---
    
    ### Getting Started
    
    #### Step 1: Scan for Stocks
    Go to the **Stock Scanner** to find stocks with strong moat characteristics:
    - Choose from predefined universes (S&P 500, Tech, Healthcare, Financial)
    - Or enter your own tickers
    - Configure moat scoring criteria
    - View ranked results with detailed analysis
    
    #### Step 2: Build Your Strategy
    Use the **Strategy Builder** to create custom trading strategies:
    - Define entry and exit rules using technical indicators
    - Configure position sizing (percentage, fixed, or risk-based)
    - Set stop loss, take profit, and trailing stops
    - Save and load strategies for reuse
    
    #### Step 3: Backtest
    Run **Backtests** to evaluate strategy performance:
    - Select stocks from scanner or enter manually
    - Choose a strategy
    - Set date range and initial capital
    - View instant results with:
        - Total return, CAGR, Sharpe ratio
        - Equity curve and drawdown charts
        - Trade-by-trade analysis
        - Win rate and profit factor
    
    ---
    
    ### Key Features
    
    **Moat Analysis**
    - Fundamental metrics: ROE, margins, debt ratios, cash flow
    - Technical indicators: Moving averages, volume, relative strength
    - Combined scoring system (0-100)
    
    **Advanced Strategy Engine**
    - Support for complex rules with AND/OR/NOT logic
    - 15+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
    - Flexible position sizing methods
    - Comprehensive risk management
    
    **Professional Backtesting**
    - Realistic commission and slippage modeling
    - Stop loss and take profit execution
    - Trailing stops
    - Detailed performance metrics
    - Interactive visualizations
    
    ---
    
    ### Example Strategies
    
    **Mean Reversion Strategy**
    ```
    Entry: rsi(14) < 30 AND price > sma(200)
    Exit: rsi(14) > 70 OR price < entry_price * 0.95
    ```
    
    **Momentum Breakout**
    ```
    Entry: price > sma(50) AND volume > sma(volume, 20) * 1.5 AND rsi(14) > 50
    Exit: price < sma(20) OR rsi(14) < 40
    ```
    
    **MACD Crossover**
    ```
    Entry: macd() > macd_signal() AND price > sma(200)
    Exit: macd() < macd_signal()
    ```
    
    ---
    
    ### Ready to Start?
    
    Click on **Stock Scanner** in the sidebar to begin finding great stocks with strong moats!
    """)
    
    # Quick action buttons
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Start Scanning", use_container_width=True):
            st.session_state.page = "🔍 Stock Scanner"
            st.rerun()
    
    with col2:
        if st.button("⚙️ Build Strategy", use_container_width=True):
            st.session_state.page = "⚙️ Strategy Builder"
            st.rerun()
    
    with col3:
        if st.button("📈 Run Backtest", use_container_width=True):
            st.session_state.page = "📈 Backtest"
            st.rerun()

elif page == "🔍 Stock Scanner":
    render_scanner_page()

elif page == "⚙️ Strategy Builder":
    render_strategy_page()

elif page == "📈 Backtest":
    render_backtest_page()
