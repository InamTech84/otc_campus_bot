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
        
        # Build sections
        cot_section = self._build_cot_section(results)
        valuation_section = self._build_valuation_section(results)
        seasonality_section = self._build_seasonality_section(results)
        
        content = f"""🎓 **OTC Campus Weekly Scanner Report**
📅 {timestamp}

**Markets Scanned:**
• Commodities: {len(results.get('commodities', []))}
• FX Futures: {len(results.get('fx', []))}
• Indices: {len(results.get('indices', []))}
• Stocks: {len(results.get('stocks', []))}

{cot_section}

{valuation_section}

{seasonality_section}

**Status:** ✅ Phase 3: Valuation & Seasonality loaded.

*Phase 4 (Market Ranking & Technical) coming next...*"""
        
        self.send_message(content)
    
    def _build_cot_section(self, results: Dict[str, Any]) -> str:
        """Build COT analysis display section"""
        commodities = results.get('commodities', [])
        fx = results.get('fx', [])
        
        cot_lines = ["**COT Net Analysis:**"]
        
        # Show commodities
        for market in commodities[:3]:
            symbol = market['symbol']
            cot_net = market.get('cot_net', {})
            bias = cot_net.get('bias', 'neutral').upper()
            score = cot_net.get('score', 0.0)
            
            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "⚪"
            cot_lines.append(f"{bias_emoji} {symbol} | {bias} (Score: {score:+.2f})")
        
        cot_lines.append("")
        
        # Show FX
        for market in fx[:2]:
            symbol = market['symbol']
            cot_net = market.get('cot_net', {})
            bias = cot_net.get('bias', 'neutral').upper()
            score = cot_net.get('score', 0.0)
            
            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "⚪"
            cot_lines.append(f"{bias_emoji} {symbol} | {bias} (Score: {score:+.2f})")
        
        return "\n".join(cot_lines)
    
    def _build_valuation_section(self, results: Dict[str, Any]) -> str:
        """Build valuation display section"""
        commodities = results.get('commodities', [])
        
        val_lines = ["**Valuation Analysis:**"]
        
        for market in commodities[:3]:
            symbol = market['symbol']
            valuation = market.get('valuation', {})
            state = valuation.get('valuation_state', 'neutral')
            dev = valuation.get('deviation_pct', 0.0)
            
            state_emoji = "🟢" if 'under' in state else "🔴" if 'over' in state else "⚪"
            val_lines.append(f"{state_emoji} {symbol} | {state} (Dev: {dev:+.1f}%)")
        
        return "\n".join(val_lines)
    
    def _build_seasonality_section(self, results: Dict[str, Any]) -> str:
        """Build seasonality display section"""
        indices = results.get('indices', [])
        
        seas_lines = ["**Seasonality (Equities):**"]
        
        for market in indices[:2]:
            symbol = market['symbol']
            seasonality = market.get('seasonality', {})
            election = seasonality.get('election_cycle', 'N/A')
            bias = seasonality.get('seasonality_bias', 'neutral').upper()
            
            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "⚪"
            seas_lines.append(f"{bias_emoji} {symbol} | {election} | {bias}")
        
        return "\n".join(seas_lines)
    
    def send_market_details(self, results: Dict[str, Any]):
        content = "📊 **Detailed Market Analysis**\n\nDetailed analysis coming in Phase 4..."
        self.send_message(content)
    
    def send_error_report(self, error_msg: str):
        content = f"❌ **Error:** {error_msg}"
        self.send_message(content)
