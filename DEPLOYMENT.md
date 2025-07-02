# Discord Bot Deployment Guide

## Current Status
✅ **Bot Code**: Ready and functional  
✅ **Dependencies**: discord.py installed  
✅ **Token**: DISCORD_BOT_TOKEN configured  
❌ **Discord Settings**: Privileged intents need enabling  

## Deployment Fixes Applied

### 1. Code Configuration ✅
- Bot is configured as a background service (not web app)
- Uses proper Discord intents for voice channel monitoring
- Entry point is `python main.py`
- Token authentication is properly configured

### 2. Environment Setup ✅
- DISCORD_BOT_TOKEN secret is configured
- Python 3.11 runtime with discord.py library
- Dependencies managed through pyproject.toml

### 3. Deployment Type ✅
- Configured for background worker deployment
- No HTTP endpoints (Discord bots don't need them)
- Proper command structure for bot execution

## Required Action: Enable Discord Intents

**You need to enable privileged intents in the Discord Developer Portal:**

1. Go to https://discord.com/developers/applications/
2. Select your bot application
3. Navigate to the "Bot" section
4. Scroll down to "Privileged Gateway Intents"
5. Enable these intents:
   - ✅ **Server Members Intent** (required for nickname management)
   - ✅ **Message Content Intent** (required for commands)

## Deployment Steps

### For Replit Deployment:
1. **Deploy as Background Worker** (not Autoscale)
   - Click "Deploy" in your Replit project
   - Choose "Reserved VM" or "Background Worker" option
   - NOT "Autoscale" (that's for web apps)

2. **Configuration**
   - Run command: `python main.py`
   - Environment: DISCORD_BOT_TOKEN (already configured)

3. **Enable Discord Intents** (see section above)

4. **Bot Permissions**
   When inviting the bot to servers, ensure it has:
   - View Channels
   - Manage Nicknames
   - Connect (for voice monitoring)

## Testing

Once deployed and intents are enabled:
1. Invite bot to your Discord server
2. Join a voice channel
3. Your nickname should change to one of: "Subject 032", "Operator-91", or "Naib-XXX"
4. Leave the voice channel
5. Your original nickname should be restored

## Commands
- `!status` - Show bot status and tracked users
- `!restore` - Manually restore a user's nickname

## Troubleshooting

### Common Issues:
1. **"Privileged intents" error** → Enable intents in Discord Developer Portal
2. **Bot offline** → Check if deployment is running as background worker
3. **No nickname changes** → Verify bot has "Manage Nicknames" permission
4. **Commands not working** → Ensure bot has proper permissions in the server

The bot is ready for deployment once you enable the Discord intents!