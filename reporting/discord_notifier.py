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

**Status:** ✅ Bot is running! Phase 2 (COT Data) loaded.

*Fundamental engines coming next...*"""
        
        self.send_message(content)
    
    def _build_cot_section(self, results: Dict[str, Any]) -> str:
        """Build COT data display section"""
        commodities = results.get('commodities', [])
        fx = results.get('fx', [])
        
        cot_lines = ["**COT Positions Loaded:**"]
        
        # Show commodities with COT
        for market in commodities[:3]:  # Show first 3
            symbol = market['symbol']
            comm_net = market.get('cot_commercial_net', 'N/A')
            retail_net = market.get('cot_retail_net', 'N/A')
            
            if comm_net != 'N/A':
                cot_lines.append(f"• {symbol} | Comm: {comm_net:,.0f} | Retail: {retail_net:,.0f}")
        
        # Show FX with COT
        for market in fx[:2]:  # Show first 2
            symbol = market['symbol']
            comm_net = market.get('cot_commercial_net', 'N/A')
            retail_net = market.get('cot_retail_net', 'N/A')
            
            if comm_net != 'N/A':
                cot_lines.append(f"• {symbol} | Comm: {comm_net:,.0f} | Retail: {retail_net:,.0f}")
        
        return "\n".join(cot_lines)
    
    def send_market_details(self, results: Dict[str, Any]):
        content = "📊 **Detailed Market Analysis**\n\nDetailed analysis coming in Phase 3..."
        self.send_message(content)
    
    def send_error_report(self, error_msg: str):
        content = f"❌ **Error:** {error_msg}"
        self.send_message(content)
