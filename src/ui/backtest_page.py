"""
Backtest execution and results UI page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from pathlib import Path

from src.backtest.engine import BacktestEngine
from src.ui.scanner_page import get_selected_stocks
from src.ui.strategy_page import get_current_strategy
from config.settings import STRATEGIES_DIR, DEFAULT_INITIAL_CAPITAL, DEFAULT_COMMISSION_RATE


def render_backtest_page():
    """Render the backtest page"""
    st.title("📈 Backtest")
    st.markdown("Run backtests and visualize P&L results instantly.")
    
    # Configuration section
    st.subheader("1. Backtest Configuration")
    
    # Stock selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Select Stocks**")
        
        stock_source = st.radio(
            "Stock Source",
            ["From Scanner", "Manual Entry"],
            horizontal=True
        )
        
        if stock_source == "From Scanner":
            available_stocks = get_selected_stocks()
            if available_stocks:
                selected_stocks = st.multiselect(
                    "Select stocks to backtest",
                    available_stocks,
                    default=available_stocks[:1] if available_stocks else []
                )
            else:
                st.warning("No stocks from scanner. Go to Scanner page first.")
                selected_stocks = []
        else:
            ticker_input = st.text_input("Enter ticker", placeholder="e.g., AAPL")
            selected_stocks = [ticker_input.strip().upper()] if ticker_input.strip() else []
    
    with col2:
        st.markdown("**Select Strategy**")
        
        # Load available strategies
        saved_strategies = list(STRATEGIES_DIR.glob("*.json"))
        
        if saved_strategies:
            strategy_names = [s.stem for s in saved_strategies]
            
            # Check if there's a current strategy
            current_strategy = get_current_strategy()
            default_idx = 0
            if current_strategy and current_strategy.get('name') in strategy_names:
                default_idx = strategy_names.index(current_strategy['name'])
            
            selected_strategy_name = st.selectbox(
                "Choose strategy",
                strategy_names,
                index=default_idx
            )
            
            # Load strategy
            strategy_path = STRATEGIES_DIR / f"{selected_strategy_name}.json"
            with open(strategy_path, 'r') as f:
                strategy = json.load(f)
        else:
            st.warning("No strategies found. Go to Strategy Builder first.")
            strategy = None
    
    # Date range and capital
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365)
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    
    with col3:
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=10000000,
            value=int(DEFAULT_INITIAL_CAPITAL),
            step=1000
        )
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            commission_rate = st.number_input(
                "Commission Rate (%)",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_COMMISSION_RATE * 100,
                step=0.01,
                format="%.3f"
            ) / 100
        
        with col2:
            slippage_rate = st.number_input(
                "Slippage Rate (%)",
                min_value=0.0,
                max_value=1.0,
                value=0.05,
                step=0.01,
                format="%.3f"
            ) / 100
    
    # Run backtest button
    st.subheader("2. Run Backtest")
    
    if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
        if not selected_stocks:
            st.error("Please select at least one stock.")
        elif not strategy:
            st.error("Please select a strategy.")
        elif start_date >= end_date:
            st.error("Start date must be before end date.")
        else:
            with st.spinner("Running backtest..."):
                # Initialize backtest engine
                engine = BacktestEngine(
                    initial_capital=initial_capital,
                    commission_rate=commission_rate,
                    slippage_rate=slippage_rate
                )
                
                # Run backtest
                if len(selected_stocks) == 1:
                    results = engine.run_backtest(
                        selected_stocks[0],
                        strategy,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                else:
                    results = engine.run_multi_stock_backtest(
                        selected_stocks,
                        strategy,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                
                # Store results in session state
                st.session_state.backtest_results = results
                
                if 'error' in results:
                    st.error(results['error'])
                else:
                    st.success("Backtest completed!")
    
    # Display results
    if 'backtest_results' in st.session_state:
        results = st.session_state.backtest_results
        
        if 'error' not in results:
            st.subheader("3. Results")
            
            metrics = results['metrics']
            
            # Summary metrics cards
            st.markdown("### Performance Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_return = metrics.get('total_return_pct', 0)
                st.metric(
                    "Total Return",
                    f"{total_return:.2f}%",
                    delta=f"${metrics.get('final_equity', 0) - metrics.get('initial_capital', 0):,.0f}"
                )
            
            with col2:
                cagr = metrics.get('cagr_pct', 0)
                st.metric("CAGR", f"{cagr:.2f}%")
            
            with col3:
                sharpe = metrics.get('sharpe_ratio', 0)
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            
            with col4:
                max_dd = metrics.get('max_drawdown_pct', 0)
                st.metric("Max Drawdown", f"{max_dd:.2f}%")
            
            # Additional metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                win_rate = metrics.get('win_rate_pct', 0)
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            with col2:
                profit_factor = metrics.get('profit_factor', 0)
                st.metric("Profit Factor", f"{profit_factor:.2f}")
            
            with col3:
                total_trades = metrics.get('total_trades', 0)
                st.metric("Total Trades", f"{total_trades}")
            
            with col4:
                avg_holding = metrics.get('avg_holding_days', 0)
                st.metric("Avg Hold Days", f"{avg_holding:.1f}")
            
            # Equity curve
            st.markdown("### Equity Curve")
            
            equity_df = results['equity_curve']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=equity_df['date'],
                y=equity_df['equity'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # Add initial capital line
            fig.add_hline(
                y=initial_capital,
                line_dash="dash",
                line_color="gray",
                annotation_text="Initial Capital"
            )
            
            fig.update_layout(
                title="Portfolio Equity Over Time",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Drawdown chart
            st.markdown("### Drawdown")
            
            # Calculate drawdown
            equity_series = equity_df['equity']
            cummax = equity_series.cummax()
            drawdown = (equity_series - cummax) / cummax * 100
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=equity_df['date'],
                y=drawdown,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color='#d62728', width=2)
            ))
            
            fig.update_layout(
                title="Drawdown Over Time",
                xaxis_title="Date",
                yaxis_title="Drawdown (%)",
                hovermode='x unified',
                template='plotly_white',
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade analysis
            st.markdown("### Trade Analysis")
            
            trades = results['trades']
            
            if trades:
                # Trade list
                trades_data = []
                for trade in trades:
                    trades_data.append({
                        'Ticker': trade.ticker,
                        'Entry Date': trade.entry_date.strftime('%Y-%m-%d'),
                        'Exit Date': trade.exit_date.strftime('%Y-%m-%d'),
                        'Entry Price': f"${trade.entry_price:.2f}",
                        'Exit Price': f"${trade.exit_price:.2f}",
                        'Quantity': trade.quantity,
                        'P&L': f"${trade.pnl:.2f}",
                        'P&L %': f"{trade.pnl_pct:.2f}%",
                        'Days': trade.holding_days
                    })
                
                trades_df = pd.DataFrame(trades_data)
                
                # Show trade table
                st.dataframe(trades_df, use_container_width=True, hide_index=True)
                
                # P&L distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### P&L Distribution")
                    
                    pnls = [t.pnl for t in trades]
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=pnls,
                        nbinsx=20,
                        marker_color='#1f77b4'
                    ))
                    
                    fig.update_layout(
                        xaxis_title="P&L ($)",
                        yaxis_title="Frequency",
                        template='plotly_white',
                        height=300,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### Win/Loss Analysis")
                    
                    winning = sum(1 for t in trades if t.pnl > 0)
                    losing = sum(1 for t in trades if t.pnl <= 0)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Pie(
                        labels=['Winning', 'Losing'],
                        values=[winning, losing],
                        marker_colors=['#2ca02c', '#d62728']
                    ))
                    
                    fig.update_layout(
                        template='plotly_white',
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Download trades
                csv = trades_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Trade History",
                    data=csv,
                    file_name="trade_history.csv",
                    mime="text/csv"
                )
            else:
                st.info("No trades executed during this period.")
