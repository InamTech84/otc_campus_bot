"""
COT Data Loader
Fetches CFTC Commitment of Traders data
"""

import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# CFTC Contract codes mapping
CFTC_CODES = {
    'CL1!': '067651',    # WTI Crude Oil
    'NG1!': '023651',    # Natural Gas
    'GC1!': '088691',    # Gold
    'SI1!': '084691',    # Silver
    'HG1!': '085692',    # Copper
    '6E1!': '099741',    # Euro FX
    '6B1!': '096742',    # British Pound
    '6A1!': '232741',    # Australian Dollar
    '6N1!': '112741',    # New Zealand Dollar
    '6S1!': '092741',    # Swiss Franc
    '6C1!': '090741',    # Canadian Dollar
    '6J1!': '097741',    # Japanese Yen
    'DX1!': '098662',    # Dollar Index
    'ES1!': '138741',    # E-mini S&P 500
    'NQ1!': '209742',    # E-mini Nasdaq
    'YM1!': '138741',    # E-mini Dow
    'RTY1!': '118741',   # E-mini Russell 2000
}

class COTLoader:
    """Loads CFTC COT data for futures"""
    
    def __init__(self, cache_dir: str = 'data/cot_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"COT Loader initialized with cache: {self.cache_dir}")
    
    def get_latest_cot_data(self, symbol: str) -> Optional[Dict]:
        """
        Get latest COT data for a symbol
        Returns: {
            'symbol': 'GC1!',
            'date': '2025-01-08',
            'commercial_net': 50000,
            'retail_net': -25000,
            'fund_manager_net': -10000,
            'commercial_long': 250000,
            'commercial_short': 200000,
            'retail_long': 50000,
            'retail_short': 75000
        }
        """
        
        if symbol not in CFTC_CODES:
            logger.warning(f"Symbol {symbol} not in CFTC codes mapping")
            return None
        
        cftc_code = CFTC_CODES[symbol]
        logger.info(f"Loading COT for {symbol} (code: {cftc_code})")
        
        try:
            # Try to load from cache first
            cached_data = self._load_from_cache(symbol)
            if cached_data:
                logger.info(f"Loaded {symbol} from cache")
                return cached_data
            
            # Fetch from CFTC if not in cache
            logger.info(f"Fetching {symbol} from CFTC...")
            data = self._fetch_from_cftc(symbol, cftc_code)
            
            if data:
                # Save to cache
                self._save_to_cache(symbol, data)
                logger.info(f"Saved {symbol} to cache")
                return data
            
            logger.warning(f"Could not fetch COT data for {symbol}")
            return None
        
        except Exception as e:
            logger.error(f"Error loading COT for {symbol}: {e}")
            return None
    
    def _fetch_from_cftc(self, symbol: str, cftc_code: str) -> Optional[Dict]:
        """Fetch from CFTC.gov official source"""
        
        try:
            # CFTC Disaggregated report URL
            # This fetches the latest weekly report
            url = f"https://www.cftc.gov/dea/futures/financial_data.csv"
            
            logger.info(f"Fetching from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(url)
            
            # Filter for our contract code
            contract_data = df[df['CFTC Code'] == cftc_code]
            
            if contract_data.empty:
                logger.warning(f"No data found for code {cftc_code}")
                return None
            
            # Get most recent row
            latest = contract_data.iloc[-1]
            
            # Extract positions
            commercial_long = float(latest.get('Commercial Long', 0))
            commercial_short = float(latest.get('Commercial Short', 0))
            noncommercial_long = float(latest.get('Noncommercial Long', 0))
            noncommercial_short = float(latest.get('Noncommercial Short', 0))
            nonreportable_long = float(latest.get('Nonreportable Long', 0))
            nonreportable_short = float(latest.get('Nonreportable Short', 0))
            
            # Calculate nets
            commercial_net = commercial_long - commercial_short
            noncommercial_net = noncommercial_long - noncommercial_short
            nonreportable_net = nonreportable_long - nonreportable_short
            
            data = {
                'symbol': symbol,
                'date': str(latest.get('Date', datetime.now().date())),
                'commercial_net': commercial_net,
                'commercial_long': commercial_long,
                'commercial_short': commercial_short,
                'noncommercial_net': noncommercial_net,
                'noncommercial_long': noncommercial_long,
                'noncommercial_short': noncommercial_short,
                'nonreportable_net': nonreportable_net,
                'nonreportable_long': nonreportable_long,
                'nonreportable_short': nonreportable_short,
            }
            
            logger.info(f"Fetched {symbol}: Commercial Net = {commercial_net}")
            return data
        
        except Exception as e:
            logger.error(f"CFTC fetch error: {e}")
            return None
    
    def _load_from_cache(self, symbol: str) -> Optional[Dict]:
        """Load COT data from local cache"""
        
        cache_file = self.cache_dir / f"{symbol}_cot.csv"
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is fresh (less than 7 days old)
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age > timedelta(days=7):
                logger.info(f"Cache for {symbol} is stale (age: {file_age.days} days)")
                return None
            
            # Load from cache
            df = pd.read_csv(cache_file)
            latest = df.iloc[-1].to_dict()
            logger.info(f"Loaded {symbol} from cache (age: {file_age.days} days)")
            return latest
        
        except Exception as e:
            logger.error(f"Cache load error for {symbol}: {e}")
            return None
    
    def _save_to_cache(self, symbol: str, data: Dict):
        """Save COT data to local cache"""
        
        cache_file = self.cache_dir / f"{symbol}_cot.csv"
        
        try:
            # Convert to DataFrame and append/save
            df = pd.DataFrame([data])
            
            if cache_file.exists():
                # Append to existing
                existing_df = pd.read_csv(cache_file)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_csv(cache_file, index=False)
            logger.info(f"Cached {symbol} data")
        
        except Exception as e:
            logger.error(f"Cache save error: {e}")
    
    def load_all_markets(self, symbols: list) -> Dict[str, Dict]:
        """Load COT data for all symbols"""
        
        results = {}
        for symbol in symbols:
            data = self.get_latest_cot_data(symbol)
            if data:
                results[symbol] = data
        
        logger.info(f"Loaded COT data for {len(results)}/{len(symbols)} markets")
        return results


def get_cot_data(symbol: str) -> Optional[Dict]:
    """Simple function to get COT data"""
    loader = COTLoader()
    return loader.get_latest_cot_data(symbol)
