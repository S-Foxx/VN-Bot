#!/usr/bin/env python3
"""
Discord Voice Channel Nickname Bot
Main entry point for the bot application.
"""

import asyncio
import logging
import os
import sys
from bot_working import bot
from config import BOT_CONFIG

def setup_logging():
    """Setup logging configuration for the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to start the Discord bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get Discord bot token from environment variable
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not set!")
        logger.error("Please set your Discord bot token: export DISCORD_BOT_TOKEN='your_token_here'")
        sys.exit(1)
    
    try:
        logger.info("Starting Discord Voice Nickname Bot...")
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
