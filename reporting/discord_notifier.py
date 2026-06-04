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
        
        content = f"""🎓 OTC Campus Weekly Scanner Report
📅 {timestamp}

Markets Scanned:
• Commodities: 5
• FX Futures: 8
• Indices: 4
• Stocks: 5

Status: Bot is running! Phase 1 complete."""
        
        self.send_message(content)
    
    def send_market_details(self, results: Dict[str, Any]):
        content = "Market details coming in Phase 2"
        self.send_message(content)
    
    def send_error_report(self, error_msg: str):
        content = f"Error: {error_msg}"
        self.send_message(content)
