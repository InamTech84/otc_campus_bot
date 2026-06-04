import logging
import requests
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DiscordNotifier:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_url = config['discord']['webhook_url']
        logger.info("DiscordNotifier initialized")
    
    def send_message(self, content: str):
        if not self.webhook_url or "PLACEHOLDER" in self.webhook_url:
            logger.warning("Webhook URL not valid")
            return False
        
        try:
            payload = {"content": content}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("Message sent to Discord")
                return True
            else:
                logger.error(f"Discord error {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False
    
    def send_summary_report(self, results: Dict[str, Any]):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        ranking_section = self._build_ranking_section(results)
        minors_section = self._build_minors_section(results)
        detailed_section = self._build_detailed_section(results)
        technical_section = self._build_technical_section(results)
        
        content = f"""🎓 **OTC Campus Weekly Scanner Report**
📅 {timestamp}

**Markets Scanned:**
• Commodities: {len(results.get('commodities', []))}
• FX Futures: {len(results.get('fx', []))}
• Forex Minors: {len(results.get('forex_minors', []))}
• Indices: {len(results.get('indices', []))}
• Stocks: {len(results.get('stocks', []))}

{ranking_section}

{minors_section}

{detailed_section}

{technical_section}

**Status:** ✅ Phase 5 Complete: Forex Minors integrated.

*Full S/D zone detection & price integration coming next...*"""
        
        self.send_message(content)
    
    def _build_ranking_section(self, results: Dict[str, Any]) -> str:
        """Build market ranking display section"""
        ranked = results.get('ranked_results', {})
        
        bullish = ranked.get('bullish_markets', [])
        bearish = ranked.get('bearish_markets', [])
        
        lines = []
        
        if bullish:
            lines.append("**🟢 BULLISH Markets (Majors):**")
            for market in bullish[:3]:
                symbol = market['symbol']
                score = market['final_score']
                conviction = market['conviction']
                lines.append(f"  {symbol} | Score: {score:+.2f} ({conviction})")
        
        lines.append("")
        
        if bearish:
            lines.append("**🔴 BEARISH Markets (Majors):**")
            for market in bearish[:3]:
                symbol = market['symbol']
                score = market['final_score']
                conviction = market['conviction']
                lines.append(f"  {symbol} | Score: {score:+.2f} ({conviction})")
        
        actionable = ranked.get('top_actionable', [])
        if actionable:
            lines.append("")
            lines.append(f"**⚡ Actionable Majors (|score| >= 1.0): {len(actionable)}**")
            for market in actionable:
                symbol = market['symbol']
                bias = "🟢 LONG" if market['final_bias'] == 'bullish' else "🔴 SHORT"
                score = market['final_score']
                lines.append(f"  {bias} {symbol} (Score: {score:+.2f})")
        
        return "\n".join(lines) if lines else "No ranked data yet"
    
    def _build_minors_section(self, results: Dict[str, Any]) -> str:
        """Build forex minors display section"""
        minors = results.get('forex_minors', [])
        
        if not minors:
            return "**📊 Forex Minors (Recommended):** No data yet"
        
lines = ["**📊 Forex Minors (Recommended by Bernd):**"]
        
        for minor in minors:
            symbol = minor['symbol']
            bias = minor['bias'].upper()
            score = minor['score']
            logic = minor.get('logic', '')
            
            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "⚪"
            lines.append(f"{bias_emoji} {symbol} | {bias} (Score: {score:+.2f}) | {logic}")
        
        return "\n".join(lines)
    
    def _build_detailed_section(self, results: Dict[str, Any]) -> str:
        """Build detailed analysis section"""
        ranked = results.get('ranked_results', {})
        top_actionable = ranked.get('top_actionable', [])
        
        lines = ["**🔍 Top Setup Details:**"]
        
        if top_actionable:
            for market in top_actionable[:2]:
                symbol = market['symbol']
                bias = market['final_bias'].upper()
                score = market['final_score']
                conviction = market['conviction'].upper()
                breakdown = market.get('breakdown', {})
                
                lines.append(f"\n**{symbol}** | {bias} ({conviction}) | Score: {score:+.2f}")
                lines.append(f"  COT Net: {breakdown.get('cot_net', 0):+.2f}")
                lines.append(f"  Valuation: {breakdown.get('valuation', 0):+.2f}")
                lines.append(f"  Seasonality: {breakdown.get('seasonality', 0):+.2f}")
        else:
            lines.append("No actionable setups with score >= 1.0 yet")
        
        return "\n".join(lines)
    
    def _build_technical_section(self, results: Dict[str, Any]) -> str:
        """Build technical zones section"""
        tech = results.get('technical_zones', {})
        
        if tech.get('status') == 'PLACEHOLDER':
            return "**🎯 Technical S/D Zones:** Awaiting price data integration"
        
        zones = tech.get('zones', [])
        if not zones:
            return "**🎯 Technical S/D Zones:** No HQ zones detected yet"
        
        lines = ["**🎯 Technical S/D Zones:**"]
        for zone in zones[:5]:
            z = zone['ltf_zone']
            direction = zone['direction']
            emoji = "🟢" if direction == "LONG" else "🔴"
            lines.append(f"{emoji} {z['timeframe']} | {z['top']:.5f} - {z['bot']:.5f} | Q: {zone['nesting_quality']:.2f}")
        
        return "\n".join(lines)
    
    def send_market_details(self, results: Dict[str, Any]):
        content = "📊 **Detailed Analysis**\n\nSee summary report above."
        self.send_message(content)
    
    def send_error_report(self, error_msg: str):
        content = f"❌ **Error:** {error_msg}"
        self.send_message(content)
