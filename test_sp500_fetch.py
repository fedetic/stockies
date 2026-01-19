"""
Test script to verify S&P 500 ticker fetching
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.scanner.screener import StockScreener

def test_sp500_fetch():
    """Test fetching S&P 500 tickers"""
    print("Testing S&P 500 ticker fetch...")
    print("-" * 50)
    
    try:
        # Fetch S&P 500 tickers
        tickers = StockScreener.get_sp500_tickers(use_cache=False)
        
        print(f"✓ Successfully fetched {len(tickers)} tickers")
        print(f"✓ Sample tickers: {', '.join(tickers[:10])}")
        
        # Verify we got more than the sample
        assert len(tickers) > 100, "Should have fetched more than 100 tickers"
        print(f"✓ Verified: Got {len(tickers)} tickers (more than sample of 30)")
        
        # Test caching
        cached_tickers = StockScreener.get_sp500_tickers(use_cache=True)
        assert len(cached_tickers) == len(tickers), "Cached list should match"
        print("✓ Caching works correctly")
        
        print("-" * 50)
        print("All tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sp500_fetch()
    sys.exit(0 if success else 1)
