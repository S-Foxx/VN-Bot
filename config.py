"""
Configuration settings for the Discord Voice Nickname Bot.
"""

# Bot configuration
BOT_CONFIG = {
    'command_prefix': '!',
    'description': '🎭 Transform your voice channels with automatic identity magic! Assigns mysterious nicknames when users join voice channels and perfectly restores them when they leave.',
}

# Nickname formats - these are the possible nickname formats the bot will use
NICKNAME_FORMATS = [
    "Subject 032",
    "Operator-91",
    "Naib-{counter:03d}"  # Will be formatted with incrementing counter
]

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'bot.log'
}
