"""
Stock scanner UI page
"""
import streamlit as st
import pandas as pd
from typing import List

from src.scanner.screener import StockScreener
from src.scanner.moat_analyzer import MoatAnalyzer
from src.utils.validators import Validators


def render_scanner_page():
    """Render the stock scanner page"""
    st.title("📊 Stock Scanner")
    st.markdown("Scan stocks for economic moat characteristics using fundamental and technical analysis.")
    
    # Initialize components
    if 'screener' not in st.session_state:
        st.session_state.screener = StockScreener()
    
    screener = st.session_state.screener
    
    # Input method selection
    st.subheader("1. Select Stocks to Scan")
    
    input_method = st.radio(
        "Input Method",
        ["Predefined Universe", "Manual Entry", "Upload CSV"],
        horizontal=True
    )
    
    tickers = []
    
    if input_method == "Predefined Universe":
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            universe = st.selectbox(
                "Select Universe",
                ["SP500", "TECH", "HEALTHCARE", "FINANCIAL"]
            )
        
        with col2:
            top_n = st.number_input("Top N Results", min_value=5, max_value=100, value=20, step=5)
        
        with col3:
            # Option to use full S&P 500 or sample for testing
            if universe == "SP500":
                use_full_sp500 = st.checkbox("Full S&P 500", value=True, 
                                            help="Uncheck to use 30-stock sample for testing")
            else:
                use_full_sp500 = False
        
        # Get tickers from universe
        if universe == 'SP500':
            if use_full_sp500:
                with st.spinner("Fetching S&P 500 ticker list..."):
                    tickers = StockScreener.get_sp500_tickers()
                st.info(f"📊 Ready to scan {len(tickers)} S&P 500 stocks")
            else:
                tickers = StockScreener.SP500_SAMPLE
                st.info(f"📊 Using sample of {len(tickers)} stocks for testing")
        else:
            universe_map = {
                'TECH': StockScreener.TECH_STOCKS,
                'HEALTHCARE': StockScreener.HEALTHCARE_STOCKS,
                'FINANCIAL': StockScreener.FINANCIAL_STOCKS
            }
            tickers = universe_map.get(universe, [])
            st.info(f"📊 Ready to scan {len(tickers)} {universe} stocks")
    
    elif input_method == "Manual Entry":
        ticker_input = st.text_area(
            "Enter Tickers (comma or space separated)",
            placeholder="AAPL, MSFT, GOOGL",
            height=100
        )
        
        if ticker_input:
            tickers = StockScreener.parse_ticker_input(ticker_input)
            
            # Validate tickers
            valid_tickers, invalid_tickers = Validators.validate_tickers(tickers)
            
            if invalid_tickers:
                st.warning(f"Invalid tickers (will be skipped): {', '.join(invalid_tickers)}")
            
            tickers = valid_tickers
    
    elif input_method == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV file with tickers", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Try to find ticker column
                ticker_col = None
                for col in df.columns:
                    if col.lower() in ['ticker', 'symbol', 'stock']:
                        ticker_col = col
                        break
                
                if ticker_col:
                    tickers = df[ticker_col].astype(str).tolist()
                    tickers = [t.strip().upper() for t in tickers if t.strip()]
                else:
                    st.error("Could not find ticker column. Please ensure CSV has a column named 'ticker', 'symbol', or 'stock'.")
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
    
    # Scoring criteria
    st.subheader("2. Configure Moat Criteria")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_moat_score = st.slider("Minimum Moat Score", 0, 100, 50, 5)
    
    with col2:
        min_fundamental = st.slider("Minimum Fundamental Score", 0, 100, 0, 5)
    
    with col3:
        min_technical = st.slider("Minimum Technical Score", 0, 100, 0, 5)
    
    # Scan button
    st.subheader("3. Run Scan")
    
    if st.button("🔍 Scan Stocks", type="primary", use_container_width=True):
        if not tickers:
            st.error("Please select or enter stocks to scan.")
        else:
            with st.spinner(f"Scanning {len(tickers)} stocks..."):
                # Run screening
                results = screener.screen_stocks(
                    tickers,
                    min_moat_score=min_moat_score,
                    min_fundamental_score=min_fundamental,
                    min_technical_score=min_technical
                )
                
                # Store results in session state
                st.session_state.scan_results = results
                
                # Limit results if from universe
                if input_method == "Predefined Universe" and not results.empty:
                    results = results.head(top_n)
                
                st.session_state.displayed_results = results
    
    # Display results
    if 'displayed_results' in st.session_state and not st.session_state.displayed_results.empty:
        st.subheader("4. Results")
        
        results_df = st.session_state.displayed_results
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Stocks Scanned", len(results_df))
        
        with col2:
            avg_moat = results_df['moat_score'].mean()
            st.metric("Average Moat Score", f"{avg_moat:.1f}")
        
        with col3:
            top_score = results_df['moat_score'].max()
            st.metric("Highest Score", f"{top_score:.1f}")
        
        # Results table
        st.markdown("### Ranked Stocks")
        
        # Format display dataframe
        display_df = results_df[['ticker', 'moat_score', 'fundamental_score', 'technical_score']].copy()
        display_df.columns = ['Ticker', 'Moat Score', 'Fundamental', 'Technical']
        
        # Format numbers
        for col in ['Moat Score', 'Fundamental', 'Technical']:
            display_df[col] = display_df[col].round(1)
        
        # Display with color coding
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export options
        st.markdown("### Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Save to watchlist
            if st.button("💾 Save to Watchlist"):
                st.session_state.watchlist = results_df['ticker'].tolist()
                st.success(f"Saved {len(results_df)} stocks to watchlist!")
        
        with col2:
            # Download CSV
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="stock_scan_results.csv",
                mime="text/csv"
            )
        
        # Detailed view
        st.markdown("### Detailed Analysis")
        
        selected_ticker = st.selectbox(
            "Select stock for detailed view",
            results_df['ticker'].tolist()
        )
        
        if selected_ticker:
            with st.expander(f"Details for {selected_ticker}", expanded=True):
                ticker_data = results_df[results_df['ticker'] == selected_ticker].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Fundamental Details**")
                    fund_details = ticker_data['fundamental_details']
                    if isinstance(fund_details, dict):
                        for key, value in fund_details.items():
                            if value is not None:
                                if isinstance(value, float):
                                    st.write(f"- {key}: {value:.2%}" if value < 1 else f"- {key}: {value:.2f}")
                                else:
                                    st.write(f"- {key}: {value}")
                
                with col2:
                    st.markdown("**Technical Details**")
                    tech_details = ticker_data['technical_details']
                    if isinstance(tech_details, dict):
                        for key, value in tech_details.items():
                            if value is not None:
                                st.write(f"- {key}: {value}")
    
    elif 'displayed_results' in st.session_state:
        st.info("No stocks match your criteria. Try adjusting the filters.")


def get_selected_stocks() -> List[str]:
    """Get list of selected stocks from scanner results"""
    if 'watchlist' in st.session_state:
        return st.session_state.watchlist
    elif 'displayed_results' in st.session_state and not st.session_state.displayed_results.empty:
        return st.session_state.displayed_results['ticker'].tolist()
    return []
