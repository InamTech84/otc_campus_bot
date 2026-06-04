import requests
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class DiscordNotifier:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.webhook_url = settings.discord_webhook

    def send_report(self, report):
        logger.info("Generating Discord report...")

        lines = []
        lines.append("# 🎓 OTC Campus Weekly Bias Scan")
        lines.append(f"Scan completed: {report.scanned_at} UTC")
        lines.append("")
        lines.append("## 🟢 Strong Bullish Bias")

        if len(report.bullish) == 0:
            lines.append("No assets with strong bullish bias this week")
        else:
            for asset in report.bullish:
                lines.append(f"✅ {asset.ticker} | Score: {asset.total_score:.0f}")

        lines.append("")
        lines.append("## 🔴 Strong Bearish Bias")

        if len(report.bearish) == 0:
            lines.append("No assets with strong bearish bias this week")
        else:
            for asset in report.bearish:
                lines.append(f"❌ {asset.ticker} | Score: {asset.total_score:.0f}")

        lines.append("")
        lines.append("---")
        lines.append("")

        if len(report.forex_majors) > 0:
            lines.append("**📊 Forex Majors:")
            for major in report.forex_majors:
                lines.append(f"✅ {major}")

        lines.append("")

        if len(report.minors) > 0:
            lines.append("**📊 Forex Minors (Recommended by Bernd):")
            for minor in report.minors:
                lines.append(f"✅ {minor}")

        lines.append("")

        if len(report.commodities) > 0:
            lines.append("**🛢️ Commodities & Energies:")
            for comm in report.commodities:
                lines.append(f"✅ {comm}")

        lines.append("")

        if len(report.indices) > 0:
            lines.append("**📈 Indices:")
            for index in report.indices:
                lines.append(f"✅ {index}")

        lines.append("")
        lines.append("---")
        lines.append("✅ All OTC Tier 2 Filters Applied")
        lines.append("✅ COT Inversion for Gold/Silver Active")
        lines.append("✅ 3 Week Sustained Bias Filter Active")

        message = "\n".join(lines)

        payload = {
            "content": message,
            "username": "OTC Bias Scanner"
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("✅ Report posted to Discord successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send report to Discord: {str(e)}")
            return False


    def send_error(self, error_message):
        if not self.webhook_url:
            return

        try:
            payload = {
                "content": f"❌ Fatal Error in Scanner: {error_message}",
                "username": "OTC Bias Scanner"
            }
            requests.post(self.webhook_url, json=payload)
        except:
            pass
