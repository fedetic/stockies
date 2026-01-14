"""
Strategy builder UI page
"""
import streamlit as st
import json
from pathlib import Path

from src.strategy.parser import StrategyParser
from config.settings import STRATEGIES_DIR


def render_strategy_page():
    """Render the strategy builder page"""
    st.title("⚙️ Strategy Builder")
    st.markdown("Create and configure custom trading strategies with advanced rules.")
    
    # Initialize parser
    if 'parser' not in st.session_state:
        st.session_state.parser = StrategyParser()
    
    parser = st.session_state.parser
    
    # Strategy management
    st.subheader("Strategy Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ New Strategy"):
            st.session_state.current_strategy = parser.create_default_strategy()
            st.rerun()
    
    with col2:
        # Load strategy
        saved_strategies = list(STRATEGIES_DIR.glob("*.json"))
        if saved_strategies:
            strategy_files = [s.stem for s in saved_strategies]
            selected_file = st.selectbox("Load Strategy", [""] + strategy_files)
            
            if selected_file:
                strategy_path = STRATEGIES_DIR / f"{selected_file}.json"
                with open(strategy_path, 'r') as f:
                    st.session_state.current_strategy = json.load(f)
                st.success(f"Loaded: {selected_file}")
    
    # Initialize current strategy if not exists
    if 'current_strategy' not in st.session_state:
        st.session_state.current_strategy = parser.create_default_strategy()
    
    strategy = st.session_state.current_strategy
    
    # Strategy configuration
    st.subheader("1. Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        strategy['name'] = st.text_input("Strategy Name", value=strategy.get('name', ''))
    
    with col2:
        strategy['description'] = st.text_input("Description", value=strategy.get('description', ''))
    
    # Entry rules
    st.subheader("2. Entry Rules")
    st.markdown("Define conditions for entering a trade. Use AND, OR, NOT for complex logic.")
    
    # Show available indicators
    with st.expander("📚 Available Indicators & Variables"):
        st.markdown("""
        **Indicators:**
        - `sma(period)` - Simple Moving Average
        - `ema(period)` - Exponential Moving Average
        - `rsi(period)` - Relative Strength Index
        - `macd()`, `macd_signal()`, `macd_hist()` - MACD indicators
        - `bb_upper()`, `bb_lower()` - Bollinger Bands
        - `atr(period)` - Average True Range
        - `stoch_k()`, `stoch_d()` - Stochastic Oscillator
        - `adx()` - Average Directional Index
        
        **Variables:**
        - `price`, `close` - Closing price
        - `open`, `high`, `low` - OHLC prices
        - `volume` - Trading volume
        - `entry_price` - Entry price (for exit rules)
        
        **Operators:**
        - Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
        - Logical: `AND`, `OR`, `NOT`
        
        **Examples:**
        - `rsi(14) < 30 AND price > sma(200)`
        - `price > ema(20) AND volume > sma(volume, 20) * 1.5`
        - `macd() > macd_signal() AND adx() > 25`
        """)
    
    strategy['entry_rules'] = st.text_area(
        "Entry Rules",
        value=strategy.get('entry_rules', ''),
        height=100,
        placeholder="e.g., rsi(14) < 30 AND price > sma(200)"
    )
    
    # Validate entry rules
    if strategy['entry_rules']:
        try:
            parser.parse_rules(strategy['entry_rules'])
            st.success("✓ Entry rules are valid")
        except Exception as e:
            st.error(f"❌ Invalid entry rules: {str(e)}")
    
    # Exit rules
    st.subheader("3. Exit Rules")
    st.markdown("Define conditions for exiting a trade.")
    
    strategy['exit_rules'] = st.text_area(
        "Exit Rules",
        value=strategy.get('exit_rules', ''),
        height=100,
        placeholder="e.g., rsi(14) > 70 OR price < entry_price * 0.95"
    )
    
    # Validate exit rules
    if strategy['exit_rules']:
        try:
            parser.parse_rules(strategy['exit_rules'])
            st.success("✓ Exit rules are valid")
        except Exception as e:
            st.error(f"❌ Invalid exit rules: {str(e)}")
    
    # Position sizing
    st.subheader("4. Position Sizing")
    
    if 'position_sizing' not in strategy:
        strategy['position_sizing'] = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        strategy['position_sizing']['method'] = st.selectbox(
            "Position Sizing Method",
            ["percentage", "fixed", "risk_based"],
            format_func=lambda x: {
                'percentage': 'Percentage of Capital',
                'fixed': 'Fixed Dollar Amount',
                'risk_based': 'Risk-Based (using ATR)'
            }[x]
        )
    
    with col2:
        if strategy['position_sizing']['method'] == 'percentage':
            strategy['position_sizing']['value'] = st.number_input(
                "Percentage of Capital (%)",
                min_value=1.0,
                max_value=100.0,
                value=float(strategy['position_sizing'].get('value', 10)),
                step=1.0
            )
        elif strategy['position_sizing']['method'] == 'fixed':
            strategy['position_sizing']['value'] = st.number_input(
                "Fixed Amount ($)",
                min_value=100.0,
                max_value=1000000.0,
                value=float(strategy['position_sizing'].get('value', 10000)),
                step=100.0
            )
        else:  # risk_based
            strategy['position_sizing']['value'] = st.number_input(
                "Risk Percentage (%)",
                min_value=0.5,
                max_value=10.0,
                value=float(strategy['position_sizing'].get('value', 2)),
                step=0.5
            )
    
    # Risk management
    st.subheader("5. Risk Management")
    
    if 'risk_management' not in strategy:
        strategy['risk_management'] = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_stop_loss = st.checkbox(
            "Use Stop Loss",
            value='stop_loss_pct' in strategy['risk_management']
        )
        
        if use_stop_loss:
            strategy['risk_management']['stop_loss_pct'] = st.number_input(
                "Stop Loss (%)",
                min_value=0.5,
                max_value=50.0,
                value=float(strategy['risk_management'].get('stop_loss_pct', 5)),
                step=0.5
            )
        elif 'stop_loss_pct' in strategy['risk_management']:
            del strategy['risk_management']['stop_loss_pct']
    
    with col2:
        use_take_profit = st.checkbox(
            "Use Take Profit",
            value='take_profit_pct' in strategy['risk_management']
        )
        
        if use_take_profit:
            strategy['risk_management']['take_profit_pct'] = st.number_input(
                "Take Profit (%)",
                min_value=1.0,
                max_value=1000.0,
                value=float(strategy['risk_management'].get('take_profit_pct', 15)),
                step=1.0
            )
        elif 'take_profit_pct' in strategy['risk_management']:
            del strategy['risk_management']['take_profit_pct']
    
    # Trailing stop
    strategy['risk_management']['trailing_stop'] = st.checkbox(
        "Use Trailing Stop",
        value=strategy['risk_management'].get('trailing_stop', False)
    )
    
    if strategy['risk_management']['trailing_stop']:
        strategy['risk_management']['trailing_stop_pct'] = st.number_input(
            "Trailing Stop (%)",
            min_value=1.0,
            max_value=50.0,
            value=float(strategy['risk_management'].get('trailing_stop_pct', 5)),
            step=0.5
        )
    
    # Save strategy
    st.subheader("6. Save Strategy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Strategy", type="primary", use_container_width=True):
            # Validate strategy
            is_valid, error_msg = parser.validate_strategy(strategy)
            
            if is_valid:
                # Save to file
                strategy_path = STRATEGIES_DIR / f"{strategy['name']}.json"
                with open(strategy_path, 'w') as f:
                    json.dump(strategy, f, indent=2)
                
                st.success(f"Strategy '{strategy['name']}' saved successfully!")
            else:
                st.error(f"Cannot save: {error_msg}")
    
    with col2:
        # Export strategy as JSON
        strategy_json = json.dumps(strategy, indent=2)
        st.download_button(
            label="📥 Export JSON",
            data=strategy_json,
            file_name=f"{strategy['name']}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Store in session state
    st.session_state.current_strategy = strategy


def get_current_strategy():
    """Get the current strategy from session state"""
    if 'current_strategy' in st.session_state:
        return st.session_state.current_strategy
    return None
