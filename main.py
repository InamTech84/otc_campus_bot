#!/usr/bin/env python3
"""
OTC Campus Bot — Main Entry Point
Runs weekly fundamental + technical analysis
"""

import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
from reporting.discord_notifier import DiscordNotifier
from workflows.weekly_scan import WeeklyScan


def load_config():
    """Load YAML configurations"""
    config_dir = Path(__file__).parent / "config"
    
    markets_file = config_dir / "markets.yaml"
    discord_file = config_dir / "discord.yaml"
    
    with open(markets_file, 'r') as f:
        markets_config = yaml.safe_load(f)
    
    with open(discord_file, 'r') as f:
        discord_config = yaml.safe_load(f)
    
    return markets_config, discord_config


def main():
    """Main execution"""
    logger.info("="*60)
    logger.info("🎓 OTC Campus Bot — Weekly Scan Starting")
    logger.info(f"Time: {datetime.utcnow().isoformat()} UTC")
    logger.info("="*60)
    
    try:
        # Load configs
        markets_config, discord_config = load_config()
        logger.info("✓ Configurations loaded")
        
        # Override webhook URL from environment if available (GitHub Actions)
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        if webhook_url:
            discord_config['discord']['webhook_url'] = webhook_url
            logger.info("✓ Discord webhook URL loaded from environment")
        
        # Initialize Discord notifier
        discord = DiscordNotifier(discord_config)
        logger.info("✓ Discord notifier initialized")
        
        # Initialize weekly scan
        scan = WeeklyScan(markets_config, discord_config)
        logger.info("✓ Weekly scan engine initialized")
        
        # Run scan
        logger.info("Starting market scan...")
        results = scan.run()
        logger.info(f"✓ Scan complete. Found {len(results)} markets")
        
        # Send summary to Discord
        logger.info("Sending Discord report...")
        discord.send_summary_report(results)
        logger.info("✓ Discord report sent")
        
        logger.info("="*60)
        logger.info("✓ Weekly scan completed successfully")
        logger.info("="*60)
        
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        try:
            discord = DiscordNotifier(discord_config)
            discord.send_error_report(str(e))
        except:
            pass
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
