"""
Weekly Scan Orchestrator
Coordinates all analysis engines
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from data.cot_loader import COTLoader
from fundamentals.cot_net import analyze_cot_net
from fundamentals.cot_index import analyze_cot_index
from fundamentals.valuation import analyze_valuation
from fundamentals.seasonality import analyze_seasonality

logger = logging.getLogger(__name__)


class WeeklyScan:
    """Main weekly scan workflow"""
    
    def __init__(self, markets_config: Dict, discord_config: Dict):
        self.markets_config = markets_config
        self.discord_config = discord_config
        self.results = {}
        self.cot_loader = COTLoader()
        logger.info("✓ COT Loader initialized")
    
    def run(self) -> Dict[str, Any]:
        """Run complete weekly scan"""
        
        logger.info("Phase 1: Initializing scan...")
        self._init_scan()
        
        logger.info("Phase 2: Loading COT data...")
        self._load_cot_data()
        
        logger.info("Phase 3: Scanning commodities...")
        self._scan_commodities()
        
        logger.info("Phase 4: Scanning FX futures...")
        self._scan_fx()
        
        logger.info("Phase 5: Scanning indices...")
        self._scan_indices()
        
        logger.info("Phase 6: Scanning stocks...")
        self._scan_stocks()
        
        logger.info("Phase 7: Running technical analysis...")
        self._run_technical()
        
        return self.results
    
    def _init_scan(self):
        """Initialize scan metadata"""
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'commodities': [],
            'fx': [],
            'indices': [],
            'stocks': [],
            'cot_data': {},
            'summary': {
                'total_markets': 0,
                'strong_bullish': 0,
                'bullish': 0,
                'neutral': 0,
                'bearish': 0,
                'strong_bearish': 0
            }
        }
        logger.info("✓ Scan initialized")
    
    def _load_cot_data(self):
        """Load COT data for all markets"""
        logger.info("Loading COT data from CFTC...")
        
        # Get all symbols that have CFTC codes
        all_markets = []
        all_markets.extend(self.markets_config.get('commodities', []))
        all_markets.extend(self.markets_config.get('fx_futures', []))
        all_markets.extend(self.markets_config.get('indices', []))
        
        symbols = [market['display_name'] for market in all_markets]
        
        # Load COT data for each symbol
        cot_data = self.cot_loader.load_all_markets(symbols)
        self.results['cot_data'] = cot_data
        
        logger.info(f"✓ Loaded COT data for {len(cot_data)} markets")
    
    def _scan_commodities(self):
        """Analyze commodity markets"""
        logger.info("Scanning commodity markets...")
        
        commodities = self.markets_config.get('commodities', [])
        logger.info(f"Found {len(commodities)} commodity markets")
        
        for market in commodities:
            symbol = market['display_name']
            logger.info(f"  → {symbol}")
            
            # Get COT data
            cot_data = self.results['cot_data'].get(symbol, {})
            
            # Analyze COT Net
            cot_net_result = analyze_cot_net(cot_data, symbol)
            
            # Analyze COT Index
            cot_index_result = analyze_cot_index(cot_data, symbol)
            
            # Analyze Valuation
            valuation_result = analyze_valuation(symbol, 'commodity')
            
            # Analyze Seasonality
            seasonality_result = analyze_seasonality(symbol, 'commodity')
            
            # Combine results
            result = {
                'symbol': symbol,
                'asset_class': 'commodity',
                'cot_net': cot_net_result,
                'cot_index': cot_index_result,
                'valuation': valuation_result,
                'seasonality': seasonality_result,
                'bias': cot_net_result.get('bias', 'neutral'),
                'score': cot_net_result.get('score', 0.0),
                'status': 'fundamental_analysis_complete'
            }
            
            self.results['commodities'].append(result)
    
    def _scan_fx(self):
        """Analyze FX futures markets"""
        logger.info("Scanning FX futures markets...")
        
        fx = self.markets_config.get('fx_futures', [])
        logger.info(f"Found {len(fx)} FX markets")
        
        for market in fx:
            symbol = market['display_name']
            logger.info(f"  → {symbol}")
            
            # Get COT data
            cot_data = self.results['cot_data'].get(symbol, {})
            
            # Analyze COT Net
            cot_net_result = analyze_cot_net(cot_data, symbol)
            
            # Analyze COT Index
            cot_index_result = analyze_cot_index(cot_data, symbol)
            
            # Analyze Valuation (vs DXY)
            valuation_result = analyze_valuation(symbol, 'forex')
            
            # Analyze Seasonality
            seasonality_result = analyze_seasonality(symbol, 'forex')
            
            # Combine results
            result = {
                'symbol': symbol,
                'asset_class': 'forex',
                'cot_net': cot_net_result,
                'cot_index': cot_index_result,
                'valuation': valuation_result,
                'seasonality': seasonality_result,
                'bias': cot_net_result.get('bias', 'neutral'),
                'score': cot_net_result.get('score', 0.0),
                'status': 'fundamental_analysis_complete'
            }
            
            self.results['fx'].append(result)
    
    def _scan_indices(self):
        """Analyze index futures"""
        logger.info("Scanning index futures...")
        
        indices = self.markets_config.get('indices', [])
        logger.info(f"Found {len(indices)} index markets")
        
        for market in indices:
            symbol = market['display_name']
            logger.info(f"  → {symbol}")
            
            # Analyze Valuation (vs ZB1!)
            valuation_result = analyze_valuation(symbol, 'index')
            
            # Analyze Seasonality (election cycle + decennial)
            seasonality_result = analyze_seasonality(symbol, 'index')
            
            result = {
                'symbol': symbol,
                'asset_class': 'index',
                'valuation': valuation_result,
                'seasonality': seasonality_result,
                'bias': seasonality_result.get('seasonality_bias', 'neutral'),
                'score': seasonality_result.get('score', 0.0),
                'status': 'fundamental_analysis_complete'
            }
            
            self.results['indices'].append(result)
    
    def _scan_stocks(self):
        """Analyze stock markets"""
        logger.info("Scanning stock markets...")
        
        stocks = self.markets_config.get('stocks', [])
        logger.info(f"Found {len(stocks)} stock markets")
        
        for market in stocks:
            symbol = market['display_name']
            logger.info(f"  → {symbol}")
            
            # Analyze Valuation (vs ZB1!)
            valuation_result = analyze_valuation(symbol, 'stock')
            
            # Analyze Seasonality (election cycle + decennial)
            seasonality_result = analyze_seasonality(symbol, 'stock')
            
            result = {
                'symbol': symbol,
                'asset_class': 'stock',
                'valuation': valuation_result,
                'seasonality': seasonality_result,
                'bias': seasonality_result.get('seasonality_bias', 'neutral'),
                'score': seasonality_result.get('score', 0.0),
                'status': 'fundamental_analysis_complete'
            }
            
            self.results['stocks'].append(result)
    
    def _run_technical(self):
        """Run technical zone analysis"""
        logger.info("Technical analysis placeholder...")
        # Phase 4 feature
        pass
