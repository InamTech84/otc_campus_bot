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
        # Load configurations
        logger.info("Loading configurations...")
        markets_config, discord_config = load_config()
        logger.info("✓ Configurations loaded successfully")
        
        # Get webhook URL from environment variable (GitHub Actions)
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        logger.info(f"Environment variable DISCORD_WEBHOOK set: {bool(webhook_url)}")
        
        if webhook_url:
            logger.info("✓ Using webhook URL from GitHub environment")
            discord_config['discord']['webhook_url'] = webhook_url
        else:
            logger.info("Using webhook URL from discord.yaml config file")
        
        # Import notifier after config is set
        from reporting.discord_notifier import DiscordNotifier
        from workflows.weekly_scan import WeeklyScan
        
        # Initialize Discord notifier
        logger.info("Initializing Discord notifier...")
        discord = DiscordNotifier(discord_config)
        logger.info("✓ Discord notifier initialized")
        
        # Initialize weekly scan
        logger.info("Initializing weekly scan engine...")
        scan = WeeklyScan(markets_config, discord_config)
        logger.info("✓ Weekly scan engine initialized")
        
        # Run scan
        logger.info("Starting market analysis...")
        results = scan.run()
        logger.info(f"✓ Market analysis complete")
        
        # Send summary to Discord
        logger.info("Sending Discord report...")
        discord.send_summary_report(results)
        logger.info("✓ Discord report sent successfully")
        
        logger.info("="*60)
        logger.info("✅ Weekly scan completed successfully!")
        logger.info("="*60)
        
        return 0
    
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure all modules are installed correctly")
        return 1
    
    except FileNotFoundError as e:
        logger.error(f"❌ Configuration file not found: {e}")
        logger.error("Make sure config/markets.yaml and config/discord.yaml exist")
        return 1
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        try:
            from reporting.discord_notifier import DiscordNotifier
            discord = DiscordNotifier(discord_config)
            discord.send_error_report(str(e))
        except:
            logger.error("Could not send error report to Discord")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
