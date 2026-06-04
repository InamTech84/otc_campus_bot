"""
Zone Nesting Engine
Implements Big Brother / Small Brother logic
HTF zones must contain LTF zones for HQ entry
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ZoneNester:
    """Manages zone nesting and coverage logic"""
    
    def __init__(self):
        logger.info("Zone Nester initialized")
    
    def filter_nested_zones(
        self,
        symbol: str,
        htf_zones: List,
        ltf_zones: List,
        direction: str
    ) -> List[Dict]:
        """
        Filter LTF zones that are nested inside HTF zones
        
        Big Brother / Small Brother principle:
        - HTF zone = Big Brother (origin, larger structure)
        - LTF zone = Small Brother (entry point, refined)
        - Only keep LTF zones that are fully inside matching HTF zone
        
        Args:
            symbol: Market symbol
            htf_zones: Zones from higher timeframe (W, D, 8H, etc)
            ltf_zones: Zones from lower timeframe (4H, 1H, etc)
            direction: 'LONG' or 'SHORT'
        
        Returns:
            List of nested zones with parent info
        """
        
        nested_zones = []
        
        if not htf_zones or not ltf_zones:
            logger.warning(f"Missing zones for {symbol} nesting")
            return nested_zones
        
        zone_type = "DEMAND" if direction == "LONG" else "SUPPLY"
        
        # Filter HTF zones matching direction
        matching_htf = [z for z in htf_zones if z.zone_type == zone_type]
        
        if not matching_htf:
            logger.info(f"No {zone_type} zones on HTF for {symbol}")
            return nested_zones
        
        # For each LTF zone, find parent HTF zone
        for ltf_zone in ltf_zones:
            if ltf_zone.zone_type != zone_type:
                continue  # Skip mismatched direction
            
            # Find parent HTF zone
            parent = None
            for htf_zone in matching_htf:
                if self._is_zone_nested(ltf_zone, htf_zone):
                    parent = htf_zone
                    break
            
            if parent:
                nested = {
                    'ltf_zone': ltf_zone.to_dict(),
                    'htf_zone': parent.to_dict(),
                    'coverage_pct': self._coverage_percentage(ltf_zone, parent),
                    'nesting_quality': self._nesting_quality(ltf_zone, parent),
                    'symbol': symbol,
                    'direction': direction,
                    'is_hq': self._is_hq_entry(ltf_zone, parent)
                }
                nested_zones.append(nested)
                logger.info(f"{symbol} | {direction} | {ltf_zone.timeframe} nested in {parent.timeframe} | Quality: {nested['nesting_quality']:.2f}")
        
        # Sort by quality
        nested_zones.sort(key=lambda x: x['nesting_quality'], reverse=True)
        
        return nested_zones
    
    def _is_zone_nested(self, ltf_zone, htf_zone) -> bool:
        """Check if LTF zone is fully inside HTF zone"""
        
        # LTF zone must be fully contained in HTF zone
        ltf_bot = ltf_zone.bot
        ltf_top = ltf_zone.top
        
        htf_bot = htf_zone.bot
        htf_top = htf_zone.top
        
        # Both boundaries must be inside
        is_nested = (ltf_bot >= htf_bot) and (ltf_top <= htf_top)
        
        return is_nested
    
    def _coverage_percentage(self, ltf_zone, htf_zone) -> float:
        """Calculate what percentage of HTF zone is covered by LTF zone"""
        
        htf_width = htf_zone.width
        if htf_width == 0:
            return 0.0
        
        # How much of HTF zone does LTF zone occupy?
        ltf_width = ltf_zone.width
        coverage = (ltf_width / htf_width) * 100
        
        return min(coverage, 100.0)
    
    def _nesting_quality(self, ltf_zone, htf_zone) -> float:
        """
        Calculate nesting quality score (0.0 to 1.0)
        
        Factors:
        - Freshness of LTF zone
        - Strength of LTF zone
        - LTF zone proximity to HTF zone center
        """
        
        # Freshness (0 to 0.3 points)
        freshness_score = 0.3 if ltf_zone.freshness else 0.1
        
        # Strength (0 to 0.3 points)
        strength_score = ltf_zone.strength * 0.3
        
        # Proximity to HTF center (0 to 0.4 points)
        htf_center = htf_zone.mid
        ltf_center = ltf_zone.mid
        
        # Distance from HTF center (as % of HTF width)
        distance = abs(ltf_center - htf_center)
        distance_pct = distance / htf_zone.width if htf_zone.width > 0 else 1.0
        
        # Closer to center = better (50% centered is ideal)
        proximity_score = 0.4 * (1.0 - min(distance_pct, 1.0))
        
        total_quality = freshness_score + strength_score + proximity_score
        
        return min(total_quality, 1.0)
    
    def _is_hq_entry(self, ltf_zone, htf_zone) -> bool:
        """
        Determine if this is a High-Quality entry zone
        
        HQ criteria:
        - LTF zone is fresh
        - LTF zone strength >= 0.5
        - LTF zone is in bottom 50% of HTF zone (discount for longs, premium for shorts)
        """
        
        if not ltf_zone.freshness:
            return False
        
        if ltf_zone.strength < 0.5:
            return False
        
        # Check position in HTF zone
        htf_bot = htf_zone.bot
        htf_top = htf_zone.top
        htf_mid = (htf_bot + htf_top) / 2
        
        # For demand: prefer zone in lower half (discount)
        # For supply: prefer zone in upper half (premium)
        if ltf_zone.zone_type == "DEMAND":
            return ltf_zone.mid < htf_mid
        else:
            return ltf_zone.mid > htf_mid
