"""
COT Net Analysis Engine
Analyzes Commercial Net positioning for bias
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class COTNetAnalyzer:
    """Analyzes COT Net positions to determine bias"""
    
    def __init__(self):
        logger.info("COT Net Analyzer initialized")
    
    def analyze(self, cot_data: Dict, symbol: str) -> Dict:
        """
        Analyze COT Net position for bias
        
        Returns: {
            'bias': 'bullish' / 'bearish' / 'neutral',
            'strength': 0.0 to 1.0,
            'commercial_net': value,
            'commercial_trend': 'rising' / 'falling' / 'stable',
            'score': -1.0 to +1.0
        }
        """
        
        if not cot_data or 'commercial_net' not in cot_data:
            logger.warning(f"No COT data for {symbol}")
            return self._neutral_result()
        
        try:
            commercial_net = float(cot_data.get('commercial_net', 0))
            commercial_long = float(cot_data.get('commercial_long', 0))
            commercial_short = float(cot_data.get('commercial_short', 0))
            
            # Analyze the position
            result = self._analyze_commercial_position(
                symbol,
                commercial_net,
                commercial_long,
                commercial_short
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing COT for {symbol}: {e}")
            return self._neutral_result()
    
    def _analyze_commercial_position(
        self,
        symbol: str,
        net_pos: float,
        long_pos: float,
        short_pos: float
    ) -> Dict:
        """Analyze commercial position"""
        
        # Determine trend direction
        if net_pos > 0:
            # Commercials are net long
            direction = "LONG"
            # Higher net long = stronger bullish
            strength = min(abs(net_pos) / 100000, 1.0)  # Normalize
            bias = "bullish"
            score = min(strength, 1.0)  # +1.0 max
        elif net_pos < 0:
            # Commercials are net short
            direction = "SHORT"
            strength = min(abs(net_pos) / 100000, 1.0)
            bias = "bearish"
            score = -min(strength, 1.0)  # -1.0 max
        else:
            # Commercials are neutral
            direction = "NEUTRAL"
            bias = "neutral"
            score = 0.0
        
        # For commodities: Commercials are hedgers
        # Long extreme = they expect prices UP
        # Short extreme = they expect prices DOWN
        
        logger.info(f"{symbol} | Commercial Net: {net_pos:,.0f} | Direction: {direction} | Score: {score:.2f}")
        
        return {
            'symbol': symbol,
            'bias': bias,
            'direction': direction,
            'strength': abs(score),
            'commercial_net': net_pos,
            'commercial_long': long_pos,
            'commercial_short': short_pos,
            'score': score,
            'engine': 'cot_net'
        }
    
    def _neutral_result(self) -> Dict:
        """Return neutral analysis"""
        return {
            'bias': 'neutral',
            'direction': 'NEUTRAL',
            'strength': 0.0,
            'commercial_net': 0,
            'score': 0.0,
            'engine': 'cot_net'
        }


def analyze_cot_net(cot_data: Dict, symbol: str) -> Dict:
    """Simple function to analyze COT net"""
    analyzer = COTNetAnalyzer()
    return analyzer.analyze(cot_data, symbol)
