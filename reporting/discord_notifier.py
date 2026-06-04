import logging
import requests
from datetime import datetime
from typing import Dict, Any, List

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
        
        # Build COT section
        cot_section = self._build_cot_section(results)
        
        content = f"""🎓 **OTC Campus Weekly Scanner Report**
📅 {timestamp}

**Markets Scanned:**
• Commodities: {len(results.get('commodities', []))}
• FX Futures: {len(results.get('fx', []))}
• Indices: {len(results.get('indices', []))}
• Stocks: {len(results.get('stocks', []))}

{cot_section}

**Status:** ✅ Phase 2B: COT Analysis Engine loaded.

*Valuation & Seasonality coming next...*"""
        
        self.send_message(content)
    
    def _build_cot_section(self, results: Dict[str, Any]) -> str:
        """Build COT analysis display section"""
        commodities = results.get('commodities', [])
        fx = results.get('fx', [])
        
        cot_lines = ["**COT Net Analysis:**"]
        
        # Show commodities analysis
        for market in commodities[:3]:
            symbol = market['symbol']
            cot_net = market.get('cot_net', {})
            bias = cot_net.get('bias', 'neutral').upper()
            comm_net = cot_net.get('commercial_net', 0)
            score = cot_net.get('score', 0.0)
            
            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "⚪"
            cot_lines.append(f"{bias_emoji} {symbol} | {bias} (Score: {score:+.2f}) | Comm Net: {comm_net:,.0f}")
        
        cot_lines.append("")
        cot_lines.append("**FX Futures COT:**")
        
        # Show FX analysis
        for market in fx[:2]:
            symbol = market['symbol']
            cot_net = market.get('cot_net', {})
            bias = cot_net.get('bias', 'neutral').upper()
            comm_net = cot_net.get('commercial_net', 0)
            score = cot_net.get('score', 0.0)
            
            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "⚪"
            cot_lines.append(f"{bias_emoji} {symbol} | {bias} (Score: {score:+.2f}) | Comm Net: {comm_net:,.0f}")
        
        return "\n".join(cot_lines)
    
    def send_market_details(self, results: Dict[str, Any]):
        content = "📊 **Detailed Market Analysis**\n\nDetailed analysis coming in Phase 3..."
        self.send_message(content)
    
    def send_error_report(self, error_msg: str):
        content = f"❌ **Error:** {error_msg}"
        self.send_message(content)
