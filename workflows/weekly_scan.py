"""
Weekly Scan Orchestrator
Coordinates all analysis engines + forex minors
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from data.cot_loader import COTLoader
from fundamentals.cot_net import analyze_cot_net
from fundamentals.cot_index import analyze_cot_index
from fundamentals.valuation import analyze_valuation
from fundamentals.seasonality import analyze_seasonality
from fundamentals.forex_minors import analyze_forex_minor
from fundamentals.market_ranking import rank_all_markets

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
        
        logger.info("Phase 5: Scanning forex minors...")
        self._scan_forex_minors()
        
        logger.info("Phase 6: Scanning indices...")
        self._scan_indices()
        
        logger.info("Phase 7: Scanning stocks...")
        self._scan_stocks()
        
        logger.info("Phase 8: Ranking markets...")
        self._rank_markets()
        
        logger.info("Phase 9: Detecting technical zones...")
        self._detect_technical_zones()
        
        return self.results
    
    def _init_scan(self):
        """Initialize scan metadata"""
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'commodities': [],
            'fx': [],
            'forex_minors': [],
            'indices': [],
            'stocks': [],
            'cot_data': {},
            'ranked_results': {},
            'technical_zones': {},
            'summary': {
                'total_markets': 0,
                'actionable_with_zones': 0
            }
        }
        logger.info("✓ Scan initialized")
    
    def _load_cot_data(self):
        """Load COT data for all markets"""
        logger.info("Loading COT data from CFTC...")
        
        all_markets = []
        all_markets.extend(self.markets_config.get('commodities', []))
        all_markets.extend(self.markets_config.get('fx_futures', []))
        all_markets.extend(self.markets_config.get('indices', []))
        
        symbols = [market['display_name'] for market in all_markets]
        
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
            
            cot_data = self.results['cot_data'].get(symbol, {})
            
            cot_net_result = analyze_cot_net(cot_data, symbol)
            cot_index_result = analyze_cot_index(cot_data, symbol)
            valuation_result = analyze_valuation(symbol, 'commodity')
            seasonality_result = analyze_seasonality(symbol, 'commodity')
            
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
            
            cot_data = self.results['cot_data'].get(symbol, {})
            
            cot_net_result = analyze_cot_net(cot_data, symbol)
            cot_index_result = analyze_cot_index(cot_data, symbol)
            valuation_result = analyze_valuation(symbol, 'forex')
            seasonality_result = analyze_seasonality(symbol, 'forex')
            
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
    
    def _scan_forex_minors(self):
        """Analyze forex minor pairs using component futures"""
        logger.info("Scanning forex minor pairs...")
        
        minors = self.markets_config.get('forex_minors', [])
        logger.info(f"Found {len(minors)} forex minor pairs")
        
        # Need ranked FX results first
        ranked_fx = self.results.get('ranked_results', {}).get('all_markets', [])
        
        for market in minors:
            symbol = market['display_name']
            logger.info(f"  → {symbol}")
            
            # Analyze using component futures
            minor_result = analyze_forex_minor(symbol, {'all_markets': ranked_fx})
            
            result = {
                'symbol': symbol,
                'asset_class': 'forex_minor',
                'components': minor_result.get('components', {}),
                'logic': minor_result.get('logic', ''),
                'bias': minor_result.get('bias', 'neutral'),
                'score': minor_result.get('score', 0.0),
                'status': 'fundamental_analysis_complete'
            }
            
            self.results['forex_minors'].append(result)
    
    def _scan_indices(self):
        """Analyze index futures"""
        logger.info("Scanning index futures...")
        
        indices = self.markets_config.get('indices', [])
        logger.info(f"Found {len(indices)} index markets")
        
        for market in indices:
            symbol = market['display_name']
            logger.info(f"  → {symbol}")
            
            valuation_result = analyze_valuation(symbol, 'index')
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
            
            valuation_result = analyze_valuation(symbol, 'stock')
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
    
    def _rank_markets(self):
        """Rank all markets by fundamental bias"""
        logger.info("Ranking markets by fundamental bias...")
        
        weights = self.markets_config.get('weights', {})
        
        ranking_weights = weights.get('commodities', {
            'cot_net': 0.25,
            'cot_index': 0.30,
            'valuation': 0.25,
            'seasonality': 0.10
        })
        
        ranked_results = rank_all_markets(self.results, ranking_weights)
        self.results['ranked_results'] = ranked_results
        
        logger.info("✓ Market ranking complete")
    
    def _detect_technical_zones(self):
        """Detect technical S/D zones (placeholder for Phase 5)"""
        logger.info("Technical zone detection - PLACEHOLDER")
        
        self.results['technical_zones'] = {
            'status': 'PLACEHOLDER',
            'note': 'Requires real OHLC price data integration'
        }
