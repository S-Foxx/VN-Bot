# Discord Voice Nickname Bot

## Overview

This is a Python Discord bot that automatically manages user nicknames based on voice channel activity. When users join voice channels, their nicknames are temporarily changed to predefined formats, and original nicknames are restored when they leave. The bot uses discord.py library and follows a modular architecture with separate configuration management.

## System Architecture

### Core Architecture
- **Language**: Python 3.8+
- **Framework**: discord.py library for Discord API integration
- **Architecture Pattern**: Event-driven bot with command handling capabilities
- **Configuration Management**: Centralized configuration through config.py
- **Logging**: Built-in Python logging with file and console output

### Bot Structure
The bot follows a class-based approach inheriting from `commands.Bot`, enabling both event handling and command processing capabilities.

## Key Components

### 1. Main Bot Class (`VoiceNicknameBot`)
- **Purpose**: Core bot functionality with voice state monitoring
- **Key Features**:
  - Voice state change detection
  - Nickname management with state tracking
  - Error handling and logging
  - Multi-user concurrent support

### 2. Configuration System (`config.py`)
- **Bot Settings**: Command prefix, description
- **Nickname Formats**: Predefined templates including counter-based formats
- **Logging Configuration**: Centralized logging setup

### 3. Entry Point (`main.py`)
- **Environment Management**: Token retrieval from environment variables
- **Logging Setup**: File and console logging configuration
- **Bot Lifecycle**: Startup, error handling, and graceful shutdown

### 4. Nickname Management System
- **State Tracking**: Dictionary-based storage of original nicknames
- **Database Storage**: PostgreSQL database for persistent nickname management
- **Guild Isolation**: Each Discord server has its own nickname collection
- **Dynamic Format**: Database nicknames formatted as "{nickname} {3-digit-counter}"
- **Restoration Logic**: Automatic restoration on voice channel exit

## Data Flow

### Voice Channel Join Process
1. User joins voice channel
2. `on_voice_state_update` event triggered
3. Original nickname stored in memory
4. New nickname assigned from predefined formats
5. Nickname updated via Discord API

### Voice Channel Leave Process
1. User leaves voice channel
2. Voice state change detected
3. Original nickname retrieved from storage
4. Nickname restored via Discord API
5. Storage entry cleaned up

### Error Handling Flow
- Permission errors gracefully handled
- API rate limiting managed through discord.py
- Comprehensive logging for debugging

## External Dependencies

### Required Libraries
- **discord.py**: Primary Discord API wrapper
- **sqlalchemy**: Database ORM for PostgreSQL integration
- **psycopg2-binary**: PostgreSQL database adapter
- **Python Standard Library**: logging, os, sys, asyncio, random, typing

### Database Requirements
- **PostgreSQL**: Database for persistent nickname storage
- **Database URL**: Configured via DATABASE_URL environment variable
- **Tables**: guilds, nicknames (auto-created on startup)

### Discord API Requirements
- **Bot Permissions**:
  - View Channels
  - Manage Nicknames
- **Intents**: voice_states, guilds, members, message_content

### Environment Dependencies
- **DISCORD_BOT_TOKEN**: Environment variable for bot authentication
- **DATABASE_URL**: PostgreSQL connection string

## Deployment Strategy

### Deployment Configuration
- **Type**: Background Worker (Reserved VM) - Discord bots don't handle HTTP requests
- **Runtime**: Python 3.11+ with discord.py library
- **Entry Point**: `python main.py`
- **Dependencies**: Managed through pyproject.toml

### Environment Setup
- Python 3.11+ runtime required
- Environment variable configuration for sensitive data
- No database dependencies (uses in-memory storage)
- **Required Secret**: DISCORD_BOT_TOKEN (configured in deployment settings)

### Discord Bot Requirements
- **Privileged Intents**: Must be enabled in Discord Developer Portal
  - Server Members Intent (for nickname management)
  - Message Content Intent (for commands)
- **Bot Permissions**:
  - View Channels
  - Manage Nicknames
  - Connect (for voice channel monitoring)

### Deployment Checklist
1. Configure DISCORD_BOT_TOKEN secret in deployment settings
2. Enable privileged intents in Discord Developer Portal
3. Ensure bot has proper permissions in target Discord servers
4. Deploy as Background Worker (not web app)

### Scaling Considerations
- In-memory storage limits horizontal scaling
- Single bot instance per token
- Memory usage scales with concurrent voice channel users

### Monitoring
- File-based logging (`bot.log`)
- Console output for real-time monitoring
- Discord presence status indication

## Recent Changes
- July 02, 2025: GitHub Portfolio Preparation ✅ COMPLETED
  - Created comprehensive .env.example template for secure configuration
  - Added professional .gitignore for sensitive data protection
  - Established MIT License for open source distribution
  - Created detailed SETUP.md installation guide
  - Rewrote README.md with professional portfolio focus highlighting technical achievements

- July 02, 2025: Professional Legal Framework ✅ COMPLETED
  - Created comprehensive Terms of Service (TERMS_OF_SERVICE.md)
  - Developed detailed Privacy Policy (PRIVACY_POLICY.md) with GDPR/CCPA considerations
  - Added legal compliance summary (LEGAL_COMPLIANCE.md)
  - Covered data minimization, user rights, and security measures
  - Established clear responsibilities for server owners and users

- July 02, 2025: Enhanced Bot Security & Marketing ✅ COMPLETED
  - Converted all 6 slash commands to owner-only access for maximum security
  - Created comprehensive, engaging bot description and marketing materials
  - Updated README.md with compelling features and use cases
  - Enhanced config.py with marketing-focused bot description
  - Added BOT_DESCRIPTION.md with complete promotional content

- July 02, 2025: Slash Command Migration ✅ COMPLETED
  - Successfully implemented 6 modern slash commands (/)
  - Commands now appear in Discord's built-in command interface  
  - Bot properly syncs slash commands on startup
  - Improved user experience with auto-complete and descriptions
  - Created proper bot invitation link with application command permissions

- July 02, 2025: Major Database Architecture Update
  - Migrated from static nicknames to PostgreSQL database system
  - Added guild-specific nickname management with owner permissions
  - Implemented Discord commands: /add_nickname, /remove_nickname, /list_nicknames
  - Created DatabaseManager class with SQLAlchemy ORM
  - Enhanced nickname format: "{nickname} {3-digit-counter}" (e.g., "Subject 001")
  - Added automatic guild registration and database table creation
  - Maintained fallback to static nicknames if database unavailable

- July 02, 2025: Applied deployment fixes for Discord bot
  - Fixed privileged intents configuration
  - Created deployment guide (DEPLOYMENT.md)
  - Updated bot configuration for proper background service deployment
  - Verified bot token configuration and dependencies

## Changelog
- July 02, 2025: Initial setup
- July 02, 2025: Deployment configuration fixes applied

## User Preferences

Preferred communication style: Simple, everyday language.