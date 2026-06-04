"""
Forex Minors Analysis Engine
Derives bias from component futures using COT data
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ForexMinorAnalyzer:
    """Analyzes forex minor pairs using component futures"""
    
    def __init__(self):
        logger.info("Forex Minor Analyzer initialized")
        
        # Component mapping: minor -> [major1, major2]
        self.components = {
            'EURJPY': ('6E1!', '6J1!'),
            'EURGBP': ('6E1!', '6B1!'),
            'AUDCAD': ('6A1!', '6C1!'),
            'EURAUD': ('6E1!', '6A1!'),
            'GBPJPY': ('6B1!', '6J1!'),
            'GBPCHF': ('6B1!', '6S1!'),
            'AUDJPY': ('6A1!', '6J1!')
        }
    
    def analyze(self, symbol: str, all_fx_results: Dict) -> Dict:
        """
        Analyze forex minor by combining component futures
        
        Args:
            symbol: Minor pair (e.g., 'EURJPY')
            all_fx_results: Dict with all FX futures analysis results
        
        Returns:
            {
                'symbol': 'EURJPY',
                'bias': 'bullish' / 'bearish' / 'neutral',
                'score': -1.0 to +1.0,
                'components': {
                    'long_component': {...},
                    'short_component': {...}
                },
                'logic': 'explanation'
            }
        """
        
        if symbol not in self.components:
            logger.warning(f"Unknown forex minor: {symbol}")
            return self._neutral_result(symbol)
        
        try:
            component1_symbol, component2_symbol = self.components[symbol]
            
            logger.info(f"Analyzing {symbol} | Components: {component1_symbol} + {component2_symbol}")
            
            # Get component analysis results
            component1_data = self._get_component_data(component1_symbol, all_fx_results)
            component2_data = self._get_component_data(component2_symbol, all_fx_results)
            
            if not component1_data or not component2_data:
                logger.warning(f"Missing component data for {symbol}")
                return self._neutral_result(symbol)
            
            # Calculate minor pair bias
            # Logic: Long the first, Short the second (e.g., EURJPY = Long EUR, Short JPY)
            result = self._calculate_minor_bias(
                symbol,
                component1_symbol,
                component1_data,
                component2_symbol,
                component2_data
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return self._neutral_result(symbol)
    
    def _get_component_data(self, component_symbol: str, all_fx_results: Dict) -> Optional[Dict]:
        """Get analysis data for component future"""
        
        # Search in all_fx_results for matching symbol
        if 'all_markets' in all_fx_results:
            for market in all_fx_results['all_markets']:
                if market.get('symbol') == component_symbol:
                    return market
        
        return None
    
    def _calculate_minor_bias(
        self,
        minor_symbol: str,
        comp1_symbol: str,
        comp1_data: Dict,
        comp2_symbol: str,
        comp2_data: Dict
    ) -> Dict:
        """
        Calculate minor pair bias by combining components
        
        For EURJPY (Long EUR, Short JPY):
        - If EUR bullish AND JPY bullish -> Mixed (EUR up, JPY up = mixed signals)
        - If EUR bullish AND JPY bearish -> Strong bullish (EUR up, JPY down = EUR appreciation)
        - If EUR bearish AND JPY bullish -> Strong bearish (EUR down, JPY down = JPY strength)
        - If EUR bearish AND JPY bearish -> Mixed (both falling)
        """
        
        # Get component biases
        comp1_cot = comp1_data.get('cot_net', {})
        comp2_cot = comp2_data.get('cot_net', {})
        
        comp1_bias = comp1_cot.get('bias', 'neutral')
        comp1_score = comp1_cot.get('score', 0.0)
        
        comp2_bias = comp2_cot.get('bias', 'neutral')
        comp2_score = comp2_cot.get('score', 0.0)
        
        # Calculate minor pair score
        # Long component1 (positive), Short component2 (negative of component2)
        # So if comp1 is bullish (+) and comp2 is bullish (+), we negate comp2
        minor_score = comp1_score - comp2_score  # Long comp1, Short comp2
        
        # Clamp to -1.0 to +1.0
        minor_score = max(-1.0, min(1.0, minor_score))
        
        # Determine bias
        if minor_score > 0.3:
            minor_bias = 'bullish'
        elif minor_score < -0.3:
            minor_bias = 'bearish'
        else:
            minor_bias = 'neutral'
        
        # Build logic explanation
        logic = self._build_logic_explanation(
            minor_symbol,
            comp1_symbol,
            comp1_bias,
            comp2_symbol,
            comp2_bias,
            minor_bias
        )
        
        logger.info(f"{minor_symbol} | {minor_bias.upper()} (Score: {minor_score:+.2f}) | {logic}")
        
        return {
            'symbol': minor_symbol,
            'asset_class': 'forex_minor',
            'bias': minor_bias,
            'score': minor_score,
            'components': {
                'long_component': {
                    'symbol': comp1_symbol,
                    'bias': comp1_bias,
                    'score': comp1_score
                },
                'short_component': {
                    'symbol': comp2_symbol,
                    'bias': comp2_bias,
                    'score': comp2_score
                }
            },
            'logic': logic,
            'engine': 'forex_minors'
        }
    
    def _build_logic_explanation(
        self,
        minor: str,
        comp1: str,
        bias1: str,
        comp2: str,
        bias2: str,
        result_bias: str
    ) -> str:
        """Build human-readable explanation"""
        
        return f"{comp1}({bias1}) vs {comp2}({bias2}) = {result_bias}"
    
    def _neutral_result(self, symbol: str) -> Dict:
        """Return neutral analysis"""
        return {
            'symbol': symbol,
            'asset_class': 'forex_minor',
            'bias': 'neutral',
            'score': 0.0,
            'components': {
                'long_component': {'bias': 'neutral', 'score': 0.0},
                'short_component': {'bias': 'neutral', 'score': 0.0}
            },
            'logic': 'No data',
            'engine': 'forex_minors'
        }


def analyze_forex_minor(symbol: str, all_fx_results: Dict) -> Dict:
    """Simple function to analyze forex minor"""
    analyzer = ForexMinorAnalyzer()
    return analyzer.analyze(symbol, all_fx_results)
