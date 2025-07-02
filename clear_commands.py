"""
Utility script to clear all slash commands and re-sync them.
This helps resolve Discord command signature mismatches.
"""

import asyncio
import discord
from discord.ext import commands
import os
import logging

async def clear_and_sync_commands():
    """Clear all commands and re-sync them."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('clear_commands')
    
    # Get bot token
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found!")
        return
    
    # Set up bot intents
    intents = discord.Intents.default()
    intents.voice_states = True
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    
    # Create a simple bot for clearing commands
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"Connected as {bot.user}")
        
        try:
            # Clear commands for each guild
            for guild in bot.guilds:
                bot.tree.clear_commands(guild=guild)
                await bot.tree.sync(guild=guild)
                logger.info(f"Cleared commands for guild: {guild.name}")
            
            # Clear all global commands
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            logger.info("Cleared all global commands")
            
            logger.info("Command clearing completed successfully!")
            
        except Exception as e:
            logger.error(f"Error clearing commands: {e}")
        
        finally:
            await bot.close()
    
    # Run the bot briefly to clear commands
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(clear_and_sync_commands())