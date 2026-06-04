"""
Supply & Demand Zone Detector
Identifies institutional S/D zones using RBR, DBR, RBD, DBD patterns
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Zone:
    """Represents a Supply or Demand Zone"""
    
    def __init__(
        self,
        symbol: str,
        zone_type: str,
        top: float,
        bot: float,
        timeframe: str,
        pattern: str,
        formation_date: str,
        freshness: bool,
        strength: float
    ):
        self.symbol = symbol
        self.zone_type = zone_type  # 'DEMAND' or 'SUPPLY'
        self.top = top
        self.bot = bot
        self.mid = (top + bot) / 2
        self.width = top - bot
        self.timeframe = timeframe
        self.pattern = pattern  # RBR, DBR, RBD, DBD
        self.formation_date = formation_date
        self.freshness = freshness
        self.strength = strength  # 0.0 to 1.0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'type': self.zone_type,
            'top': self.top,
            'bot': self.bot,
            'mid': self.mid,
            'width': self.width,
            'timeframe': self.timeframe,
            'pattern': self.pattern,
            'formation_date': self.formation_date,
            'fresh': self.freshness,
            'strength': self.strength
        }


class SDDetector:
    """Detects Supply & Demand Zones"""
    
    def __init__(self):
        logger.info("S/D Detector initialized")
    
    def detect_zones(
        self,
        symbol: str,
        timeframe: str,
        ohlc_data: List[Dict]
    ) -> List[Zone]:
        """
        Detect S/D zones from OHLC data
        
        Args:
            symbol: Market symbol
            timeframe: Timeframe (1H, 4H, D, W, etc)
            ohlc_data: List of OHLC candles with ['open', 'high', 'low', 'close', 'time']
        
        Returns:
            List of Zone objects
        """
        
        if not ohlc_data or len(ohlc_data) < 10:
            logger.warning(f"Not enough data for {symbol}")
            return []
        
        zones = []
        
        try:
            # Scan for base formations (2-6 tight candles)
            for i in range(6, len(ohlc_data) - 2):
                # Check for potential base
                base_info = self._find_base(ohlc_data, i)
                
                if base_info:
                    base_idx, base_top, base_bot = base_info
                    
                    # Check for explosive departure after base
                    departure = self._check_departure(ohlc_data, i)
                    
                    if departure:
                        dep_idx, is_bullish = departure
                        
                        # Create zone
                        zone_type = "DEMAND" if is_bullish else "SUPPLY"
                        pattern = self._identify_pattern(ohlc_data, base_idx, i, is_bullish)
                        
                        # Check freshness (zone not retested after formation)
                        fresh = self._check_freshness(ohlc_data, i, base_top, base_bot, is_bullish)
                        
                        # Calculate strength
                        strength = self._calculate_strength(
                            ohlc_data[i],
                            base_top - base_bot,
                            is_bullish
                        )
                        
                        zone = Zone(
                            symbol=symbol,
                            zone_type=zone_type,
                            top=base_top,
                            bot=base_bot,
                            timeframe=timeframe,
                            pattern=pattern,
                            formation_date=str(ohlc_data[i].get('time', 'N/A')),
                            freshness=fresh,
                            strength=strength
                        )
                        
                        zones.append(zone)
                        logger.info(f"{symbol} {timeframe} | {zone_type} {pattern} @ {zone.mid:.4f} | Fresh: {fresh} | Str: {strength:.2f}")
            
            logger.info(f"Found {len(zones)} zones for {symbol} on {timeframe}")
            return zones
        
        except Exception as e:
            logger.error(f"Error detecting zones for {symbol}: {e}")
            return []
    
    def _find_base(self, ohlc_data: List[Dict], index: int) -> Optional[Tuple]:
        """
        Find a tight consolidation base (2-6 candles)
        
        Returns: (base_start_index, base_high, base_low) or None
        """
        
        if index < 2:
            return None
        
        # Look back for tight consolidation
        for base_len in range(2, 7):  # 2 to 6 candles
            if index - base_len < 0:
                continue
            
            # Get range of potential base
            base_candles = ohlc_data[index - base_len:index]
            
            base_high = max(c['high'] for c in base_candles)
            base_low = min(c['low'] for c in base_candles)
            base_range = base_high - base_low
            
            # Check if tight (narrow range)
            avg_range = base_range / base_len
            if avg_range < 0.001:  # Very tight, adjust threshold as needed
                return (index - base_len, base_high, base_low)
        
        return None
    
    def _check_departure(self, ohlc_data: List[Dict], from_index: int) -> Optional[Tuple]:
        """
        Check for explosive move after base
        
        Returns: (departure_index, is_bullish) or None
        """
        
        if from_index >= len(ohlc_data) - 1:
            return None
        
        next_candle = ohlc_data[from_index + 1]
        
        # Check for explosive up move (bullish departure)
        if next_candle['close'] > next_candle['open']:
            body = next_candle['close'] - next_candle['open']
            if body > 0.0005:  # Strong bullish body
                return (from_index + 1, True)
        
        # Check for explosive down move (bearish departure)
        if next_candle['close'] < next_candle['open']:
            body = next_candle['open'] - next_candle['close']
            if body > 0.0005:  # Strong bearish body
                return (from_index + 1, False)
        
        return None
    
    def _identify_pattern(self, ohlc_data: List[Dict], base_idx: int, depart_idx: int, bullish: bool) -> str:
        """
        Identify zone pattern (RBR, DBR, RBD, DBD)
        """
        
        if base_idx < 1:
            return "RBR" if bullish else "DBR"
        
        # Rally-Base-Rally (RBR) = demand zone
        # Drop-Base-Drop (DBD) = supply zone
        # Rally-Base-Drop (RBD) = could be either
        # Drop-Base-Rally (DBR) = could be either
        
        prev_candle = ohlc_data[base_idx - 1]
        
        was_rallying = prev_candle['close'] > prev_candle['open']
        
        if bullish:
            return "RBR" if was_rallying else "DBR"
        else:
            return "DBD" if not was_rallying else "RBD"
    
    def _check_freshness(self, ohlc_data: List[Dict], formation_idx: int, top: float, bot: float, bullish: bool) -> bool:
        """
        Check if zone is fresh (untested after formation)
        """
        
        if formation_idx >= len(ohlc_data) - 1:
            return True  # Just formed, definitely fresh
        
        # Check if price has retested the zone since formation
        for i in range(formation_idx + 1, len(ohlc_data)):
            candle = ohlc_data[i]
            
            if bullish:
                # For demand, check if price dipped into zone
                if candle['low'] <= top and candle['low'] >= bot:
                    return False  # Zone was retested
            else:
                # For supply, check if price rallied into zone
                if candle['high'] >= bot and candle['high'] <= top:
                    return False  # Zone was retested
        
        return True
    
    def _calculate_strength(self, departure_candle: Dict, base_width: float, bullish: bool) -> float:
        """
        Calculate zone strength (0.0 to 1.0)
        
        Based on departure candle size and base width
        """
        
        if bullish:
            body = departure_candle['close'] - departure_candle['open']
            wick = departure_candle['high'] - departure_candle['close']
        else:
            body = departure_candle['open'] - departure_candle['close']
            wick = departure_candle['close'] - departure_candle['low']
        
        # Strength = body size / (base width + body)
        if base_width > 0:
            strength = min(body / (base_width + body), 1.0)
        else:
            strength = min(body / 0.001, 1.0)
        
        return max(0.1, strength)  # Min 0.1, max 1.0


def detect_sd_zones(
    symbol: str,
    timeframe: str,
    ohlc_data: List[Dict]
) -> List[Zone]:
    """Simple function to detect zones"""
    detector = SDDetector()
    return detector.detect_zones(symbol, timeframe, ohlc_data)
