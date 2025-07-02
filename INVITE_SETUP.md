# Discord Bot Invitation Setup

## ✅ Status: Slash Commands Working!

Your bot is now successfully running with **5 slash commands synced** to Discord!

## 🔗 Bot Invitation Link

To re-invite your bot with proper slash command permissions, use this link:

```
https://discord.com/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=268435456&scope=bot%20applications.commands
```

## 🔧 How to Get Your Client ID

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Copy the **Application ID** (this is your Client ID)
4. Replace `YOUR_BOT_CLIENT_ID` in the link above with this ID

## 🎯 Required Permissions

The invitation link includes these essential permissions:
- **Manage Nicknames** (268435456) - Required for changing user nicknames
- **Bot Scope** - Standard bot permissions
- **Application Commands** - Required for slash commands to work

## 🚀 Available Slash Commands

Once you re-invite the bot, these commands will be available:

- `/status` - Display bot status and tracked users
- `/restore` - Manually restore a user's nickname
- `/add_nickname` - Add a new nickname to the server (requires Manage Nicknames permission)
- `/remove_nickname` - Remove a nickname from the server (owner only)
- `/list_nicknames` - List all active nicknames for this server
- `/bot_health` - Comprehensive bot status check (owner only)

## 📝 Next Steps

1. **Get your Client ID** from the Discord Developer Portal
2. **Replace** `YOUR_BOT_CLIENT_ID` in the invitation link
3. **Re-invite** the bot using the updated link
4. **Test** the slash commands - they should appear when you type `/` in Discord
5. **Add some nicknames** using `/add_nickname` to populate your database

## 🎮 How It Works

- **Voice Join**: When users join voice channels, they get random nicknames like "Subject 001", "Operative 042"
- **Voice Leave**: Original nicknames are automatically restored when they leave
- **Database**: Each Discord server has its own collection of custom nicknames
- **Permissions**: Only users with "Manage Nicknames" can add nicknames, only server owners can remove them

## 🔄 For Future Updates

The current bot architecture allows for seamless updates without requiring users to re-invite the bot. Future command changes will sync automatically.

## ⚠️ Important Notes

- The bot requires "Manage Nicknames" permission to work
- Make sure the bot role is positioned above the users you want to nickname
- The database automatically creates tables and manages guild registration
- All nickname changes are logged for troubleshooting