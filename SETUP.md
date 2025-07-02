# Discord Voice Nickname Bot - Setup Guide

## Prerequisites

- Python 3.8+ installed
- Discord Bot Token (from Discord Developer Portal)
- PostgreSQL database (local or hosted)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/discord-voice-nickname-bot.git
cd discord-voice-nickname-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or if using the project file:
```bash
pip install discord.py sqlalchemy psycopg2-binary
```

### 3. Environment Configuration
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual credentials:
   ```env
   DISCORD_BOT_TOKEN=your_actual_bot_token_here
   DATABASE_URL=postgresql://username:password@host:port/database_name
   ```

### 4. Discord Bot Setup

#### Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name your bot
3. Go to "Bot" section and click "Add Bot"
4. Copy the bot token and add it to your `.env` file

#### Set Bot Permissions
Required permissions:
- View Channels
- Manage Nicknames
- Use Slash Commands

#### Enable Privileged Intents
In the Bot section, enable:
- Server Members Intent
- Message Content Intent

### 5. Database Setup

#### Option A: Local PostgreSQL
1. Install PostgreSQL on your system
2. Create a database:
   ```sql
   CREATE DATABASE nickname_bot;
   ```
3. Update DATABASE_URL in `.env` with your local credentials

#### Option B: Hosted Database
Use services like:
- Railway
- Supabase
- Heroku Postgres
- PlanetScale

### 6. Run the Bot
```bash
python main.py
```

The bot will:
- Connect to Discord
- Initialize the database tables
- Sync slash commands
- Start monitoring voice channels

## Bot Invitation

### Generate Invite Link
1. Go to Discord Developer Portal > OAuth2 > URL Generator
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select permissions:
   - View Channels
   - Manage Nicknames
4. Copy the generated URL and invite to your server

### Test the Bot
1. Join a voice channel
2. Your nickname should change to a random format like "Subject 001"
3. Leave the voice channel
4. Your original nickname should be restored

## Available Commands (Server Owner Only)

- `/status` - View bot status and active users
- `/restore [member]` - Manually restore a user's nickname
- `/add_nickname <nickname>` - Add a new nickname to the pool
- `/remove_nickname <nickname>` - Remove a nickname from the pool
- `/list_nicknames` - View all nicknames for your server
- `/bot_health` - Comprehensive bot status check

## Default Nicknames

The bot starts with these nicknames:
- Baron
- Muab-dib
- Operator
- Subject
- Naib

Server owners can add more using `/add_nickname`.

## Troubleshooting

### Bot Not Responding
1. Check bot token is correct
2. Verify bot has proper permissions
3. Ensure privileged intents are enabled

### Database Connection Issues
1. Verify DATABASE_URL format
2. Check database credentials
3. Ensure database server is accessible

### Nickname Changes Not Working
1. Check bot has "Manage Nicknames" permission
2. Verify bot role is higher than target user roles
3. Some users (server owner, admin roles) may be immune

### Commands Not Appearing
1. Wait a few minutes for Discord to sync commands
2. Try rejoining the server
3. Check bot has "Use Slash Commands" permission

## Logs and Monitoring

The bot creates a `bot.log` file with detailed operation logs. Check this file for debugging information.

## Support

For issues:
1. Check the logs (`bot.log`)
2. Verify your configuration
3. Review Discord permissions
4. Check database connectivity

---

**Note:** This bot requires proper Discord permissions and database access to function correctly. Ensure all setup steps are completed before use.