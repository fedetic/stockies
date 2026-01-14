"""
Technical indicator calculations
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple


class Indicators:
    """Technical indicator calculations for trading strategies"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average
        
        Args:
            data: Price series
            period: Number of periods
            
        Returns:
            SMA series
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average
        
        Args:
            data: Price series
            period: Number of periods
            
        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def wma(data: pd.Series, period: int) -> pd.Series:
        """
        Weighted Moving Average
        
        Args:
            data: Price series
            period: Number of periods
            
        Returns:
            WMA series
        """
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), 
            raw=True
        )
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index
        
        Args:
            data: Price series
            period: Number of periods (default 14)
            
        Returns:
            RSI series (0-100)
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(
        data: pd.Series, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Args:
            data: Price series
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        fast_ema = Indicators.ema(data, fast_period)
        slow_ema = Indicators.ema(data, slow_period)
        
        macd_line = fast_ema - slow_ema
        signal_line = Indicators.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        data: pd.Series, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Args:
            data: Price series
            period: Number of periods (default 20)
            std_dev: Number of standard deviations (default 2)
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        middle_band = Indicators.sma(data, period)
        std = data.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average True Range
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods (default 14)
            
        Returns:
            ATR series
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def stochastic(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        k_period: int = 14, 
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: %K period (default 14)
            d_period: %D period (default 3)
            
        Returns:
            Tuple of (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average Directional Index
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods (default 14)
            
        Returns:
            ADX series
        """
        # Calculate +DM and -DM
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        # Calculate ATR
        atr = Indicators.atr(high, low, close, period)
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume
        
        Args:
            close: Close price series
            volume: Volume series
            
        Returns:
            OBV series
        """
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Volume Weighted Average Price
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            volume: Volume series
            
        Returns:
            VWAP series
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        return vwap
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """
        Commodity Channel Index
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods (default 20)
            
        Returns:
            CCI series
        """
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )
        
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        
        return cci
    
    @staticmethod
    def roc(data: pd.Series, period: int = 12) -> pd.Series:
        """
        Rate of Change
        
        Args:
            data: Price series
            period: Number of periods (default 12)
            
        Returns:
            ROC series (percentage)
        """
        roc = ((data - data.shift(period)) / data.shift(period)) * 100
        return roc
    
    @staticmethod
    def momentum(data: pd.Series, period: int = 10) -> pd.Series:
        """
        Momentum
        
        Args:
            data: Price series
            period: Number of periods (default 10)
            
        Returns:
            Momentum series
        """
        return data.diff(period)
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Williams %R
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods (default 14)
            
        Returns:
            Williams %R series (-100 to 0)
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        
        return williams_r
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all common indicators for a DataFrame
        
        Args:
            df: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)
            
        Returns:
            DataFrame with all indicators added
        """
        df = df.copy()
        
        # Moving averages
        for period in [10, 20, 50, 100, 200]:
            df[f'SMA_{period}'] = Indicators.sma(df['Close'], period)
            df[f'EMA_{period}'] = Indicators.ema(df['Close'], period)
        
        # RSI
        df['RSI_14'] = Indicators.rsi(df['Close'], 14)
        
        # MACD
        macd, signal, hist = Indicators.macd(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = Indicators.bollinger_bands(df['Close'])
        df['BB_Upper'] = bb_upper
        df['BB_Middle'] = bb_middle
        df['BB_Lower'] = bb_lower
        
        # ATR
        df['ATR_14'] = Indicators.atr(df['High'], df['Low'], df['Close'], 14)
        
        # Stochastic
        k, d = Indicators.stochastic(df['High'], df['Low'], df['Close'])
        df['Stoch_K'] = k
        df['Stoch_D'] = d
        
        # ADX
        df['ADX_14'] = Indicators.adx(df['High'], df['Low'], df['Close'], 14)
        
        # Volume indicators
        df['OBV'] = Indicators.obv(df['Close'], df['Volume'])
        df['VWAP'] = Indicators.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        
        # CCI
        df['CCI_20'] = Indicators.cci(df['High'], df['Low'], df['Close'], 20)
        
        # ROC
        df['ROC_12'] = Indicators.roc(df['Close'], 12)
        
        # Williams %R
        df['Williams_R'] = Indicators.williams_r(df['High'], df['Low'], df['Close'], 14)
        
        return df
