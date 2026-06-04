"""
Market Ranking Engine
Combines all fundamental engines into weighted bias scores
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketRanker:
    """Ranks markets by fundamental bias"""
    
    def __init__(self, weights: Dict[str, float]):
        """
        Initialize with weights
        weights = {
            'cot_net': 0.25,
            'cot_index': 0.30,
            'valuation': 0.25,
            'seasonality': 0.20
        }
        """
        self.weights = weights
        logger.info(f"Market Ranker initialized with weights: {weights}")
    
    def rank_markets(self, all_results: Dict) -> Dict:
        """
        Rank all markets by fundamental bias
        
        Returns:
            'all_markets': [all markets with scores],
            'bullish_markets': [sorted bullish],
            'bearish_markets': [sorted bearish],
            'neutral_markets': [sorted neutral],
            'top_actionable': [top 5 by |score|]
        """
        
        logger.info("Ranking all markets...")
        
        all_markets = []
        
        # Process commodities
        for market in all_results.get('commodities', []):
            ranked = self._score_market(market, 'commodity')
            all_markets.append(ranked)
        
        # Process FX
        for market in all_results.get('fx', []):
            ranked = self._score_market(market, 'fx')
            all_markets.append(ranked)
        
        # Process Indices
        for market in all_results.get('indices', []):
            ranked = self._score_market(market, 'index')
            all_markets.append(ranked)
        
        # Process Stocks
        for market in all_results.get('stocks', []):
            ranked = self._score_market(market, 'stock')
            all_markets.append(ranked)
        
        # Sort by bias score
        all_markets_sorted = sorted(all_markets, key=lambda x: abs(x['final_score']), reverse=True)
        
        # Categorize
        bullish = [m for m in all_markets_sorted if m['final_bias'] == 'bullish']
        bearish = [m for m in all_markets_sorted if m['final_bias'] == 'bearish']
        neutral = [m for m in all_markets_sorted if m['final_bias'] == 'neutral']
        
        # Top actionable (score > threshold)
        top_actionable = [m for m in all_markets_sorted if abs(m['final_score']) >= 1.0]
        
        logger.info(f"Ranked {len(all_markets)} markets")
        logger.info(f"  Bullish: {len(bullish)}")
        logger.info(f"  Bearish: {len(bearish)}")
        logger.info(f"  Neutral: {len(neutral)}")
        logger.info(f"  Actionable (|score| >= 1.0): {len(top_actionable)}")
        
        return {
            'all_markets': all_markets_sorted,
            'bullish_markets': bullish,
            'bearish_markets': bearish,
            'neutral_markets': neutral,
            'top_actionable': top_actionable[:5],  # Top 5
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _score_market(self, market: Dict, asset_class: str) -> Dict:
        """
        Calculate final weighted bias score for a market
        
        Returns market with added fields:
            'final_score': -2.0 to +2.0
            'final_bias': 'bullish' / 'bearish' / 'neutral'
            'conviction': 'strong' / 'medium' / 'weak'
            'breakdown': {component scores}
        """
        
        symbol = market['symbol']
        
        # Get scores from each engine
        cot_net_score = market.get('cot_net', {}).get('score', 0.0)
        cot_index_score = market.get('cot_index', {}).get('score', 0.0)
        valuation_score = market.get('valuation', {}).get('score', 0.0)
        seasonality_score = market.get('seasonality', {}).get('score', 0.0)
        
        # Apply weights
        weighted_score = (
            cot_net_score * self.weights.get('cot_net', 0.25) +
            cot_index_score * self.weights.get('cot_index', 0.30) +
            valuation_score * self.weights.get('valuation', 0.25) +
            seasonality_score * self.weights.get('seasonality', 0.20)
        )
        
        # Scale to -2.0 to +2.0
        final_score = weighted_score * 2.0
        final_score = max(-2.0, min(2.0, final_score))  # Clamp
        
        # Determine bias
        if final_score > 0.5:
            final_bias = 'bullish'
        elif final_score < -0.5:
            final_bias = 'bearish'
        else:
            final_bias = 'neutral'
        
        # Determine conviction
        abs_score = abs(final_score)
        if abs_score >= 1.5:
            conviction = 'strong'
        elif abs_score >= 0.8:
            conviction = 'medium'
        else:
            conviction = 'weak'
        
        logger.info(f"{symbol} | Bias: {final_bias} ({conviction}) | Score: {final_score:+.2f}")
        
        # Add ranking info to market dict
        ranked_market = dict(market)
        ranked_market['final_score'] = final_score
        ranked_market['final_bias'] = final_bias
        ranked_market['conviction'] = conviction
        ranked_market['breakdown'] = {
            'cot_net': cot_net_score,
            'cot_index': cot_index_score,
            'valuation': valuation_score,
            'seasonality': seasonality_score
        }
        
        return ranked_market


def rank_all_markets(all_results: Dict, weights: Dict[str, float]) -> Dict:
    """Simple function to rank markets"""
    ranker = MarketRanker(weights)
    return ranker.rank_markets(all_results)
