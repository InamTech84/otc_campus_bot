"""
Discord Webhook Notifier
Sends formatted market analysis to Discord
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Sends messages to Discord via webhook"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_url = config['discord']['webhook_url']
        self.colors = config['discord']['colors']
    
    def send_message(self, content: str, embeds: List[Dict] = None):
        """Send message to Discord"""
        if not self.webhook_url or self.webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
            logger.warning("Discord webhook URL not configured. Skipping send.")
            logger.info(f"Would send: {content}")
            return False
        
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Discord message sent successfully")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False
    
    def send_summary_report(self, results: Dict[str, Any]):
        """Send weekly summary report"""
        timestamp = datetime.utcnow().strftime(self.config['messages']['timestamp_format'])
        
        # Summary message
        summary_content = f"""
🎓 **OTC Campus Weekly Scanner Report**
📅 {timestamp}

**Markets Scanned:**
• Commodities: 5
• FX Futures: 8
• Indices: 4
• Stocks: 5

**Status:** Scan in progress — engine modules being built

*Phase 1: Infrastructure setup*
*Phase 2: Fundamental engines*
*Phase 3: Technical zone detection*
*Phase 4: Chart rendering*
        """
        
        # Send summary
        self.send_message(summary_content)
        
        # Send detailed per-market embeds
        self.send_market_details(results)
    
    def send_market_details(self, results: Dict[str, Any]):
        """Send per-market detail embeds"""
        # Placeholder for Phase 2+
        content = "📊 **Detailed Market Analysis**\n\nDetailed fundamental and technical analysis coming in Phase 2..."
        self.send_message(content)
    
    def send_error_report(self, error_msg: str):
        """Send error notification"""
        content = f"""
❌ **OTC Campus Bot Error**
Time: {datetime.utcnow().isoformat()} UTC
Error: {error_msg}
        """
        self.send_message(content)


class EmbedBuilder:
    """Helper to build Discord embeds"""
    
    @staticmethod
    def create_market_embed(
        title: str,
        bias: str,
        score: float,
        color: int,
        fields: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create formatted market embed"""
        
        embed = {
            "title": title,
            "description": f"**Bias:** {bias}\n**Score:** {score:.1f}/100",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": fields or []
        }
        
        return embed
