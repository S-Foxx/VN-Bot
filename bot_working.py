"""
Discord Voice Channel Nickname Bot with Working Slash Commands
Handles voice state changes and nickname management using modern Discord slash commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from typing import Dict, Optional
from config import BOT_CONFIG
from models import DatabaseManager, Guild, Nickname

class VoiceNicknameBot(commands.Bot):
    """Discord bot that manages nicknames based on voice channel activity."""
    
    def __init__(self):
        # Set up bot intents
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',  # Won't be used, but required
            intents=intents,
            help_command=None
        )
        
        # Dictionary to store original nicknames: {user_id: original_nickname}
        self.original_nicknames: Dict[int, str] = {}
        
        # Set up logging
        self.logger = logging.getLogger('bot')
        
        # Initialize database manager
        try:
            self.db = DatabaseManager()
            self.db.create_tables()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self.db = None
    
    async def setup_hook(self):
        """Called when the bot starts - sync slash commands."""
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        self.logger.info(f"{self.user} has connected to Discord!")
        self.logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Register all guilds in database
        if self.db:
            for guild in self.guilds:
                try:
                    self.db.ensure_guild_exists(guild.id, guild.name, guild.owner_id or 0)
                    self.logger.info(f"Registered guild: {guild.name} (ID: {guild.id})")
                except Exception as e:
                    self.logger.error(f"Failed to register guild {guild.name}: {e}")

    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        if self.db:
            try:
                self.db.ensure_guild_exists(guild.id, guild.name, guild.owner_id or 0)
                self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
            except Exception as e:
                self.logger.error(f"Failed to register new guild {guild.name}: {e}")

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state changes (join/leave voice channels)."""
        # Skip bots
        if member.bot:
            return
        
        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            await self.handle_voice_join(member)
        
        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            await self.handle_voice_leave(member)

    async def handle_voice_join(self, member: discord.Member):
        """Handle when a user joins a voice channel."""
        try:
            # Store original nickname
            original_nick = member.display_name
            self.original_nicknames[member.id] = original_nick
            
            # Generate new nickname
            new_nickname = self.generate_nickname(member.guild.id)
            
            if new_nickname:
                await member.edit(nick=new_nickname)
                self.logger.info(f"Changed {member.display_name}'s nickname to '{new_nickname}'")
            
        except discord.Forbidden:
            self.logger.warning(f"No permission to change nickname for {member.display_name}")
        except Exception as e:
            self.logger.error(f"Error handling voice join for {member.display_name}: {e}")

    async def handle_voice_leave(self, member: discord.Member):
        """Handle when a user leaves a voice channel."""
        try:
            # Restore original nickname if we have it stored
            if member.id in self.original_nicknames:
                original_nick = self.original_nicknames[member.id]
                
                # Only restore if it's not their username (avoid "None" nicknames)
                if original_nick != member.name:
                    await member.edit(nick=original_nick)
                else:
                    await member.edit(nick=None)  # Reset to username
                
                # Clean up storage
                del self.original_nicknames[member.id]
                self.logger.info(f"Restored {member.display_name}'s nickname to '{original_nick}'")
            
        except discord.Forbidden:
            self.logger.warning(f"No permission to restore nickname for {member.display_name}")
        except Exception as e:
            self.logger.error(f"Error handling voice leave for {member.display_name}: {e}")

    def generate_nickname(self, guild_id: int) -> Optional[str]:
        """Generate a random nickname from the database for the specified guild."""
        try:
            if self.db:
                nickname = self.db.get_random_nickname(guild_id)
                if nickname:
                    return nickname
                else:
                    self.logger.warning(f"No nicknames available for guild {guild_id}")
        except Exception as e:
            self.logger.error(f"Error generating nickname for guild {guild_id}: {e}")
        
        # Fallback to static nicknames if database unavailable
        fallback_nicknames = BOT_CONFIG['nickname_formats']
        selected = random.choice(fallback_nicknames)
        counter = random.randint(1, 999)
        return f"{selected} {counter:03d}"

# Create a global bot instance
bot = VoiceNicknameBot()

# Slash Commands - Now properly defined with bot instance
@bot.tree.command(name="status", description="Display bot status and tracked users (owner only)")
async def status_command(interaction: discord.Interaction):
    """Display bot status and tracked users."""
    try:
        # Check if user is guild owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can use this command.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🤖 Voice Nickname Bot Status",
            description=f"Currently active in **{interaction.guild.name}**",
            color=discord.Color.green()
        )
        
        # Show tracked users
        if bot.original_nicknames:
            tracked_users = []
            for user_id in bot.original_nicknames:
                member = interaction.guild.get_member(user_id)
                if member:
                    tracked_users.append(f"• {member.display_name}")
            
            if tracked_users:
                embed.add_field(
                    name="👥 Currently Tracked Users",
                    value="\n".join(tracked_users[:10]),  # Limit to 10
                    inline=False
                )
        
        # Database status
        if bot.db:
            try:
                nicknames = bot.db.get_guild_nicknames(interaction.guild.id)
                embed.add_field(
                    name="📊 Database Status",
                    value=f"✅ Connected\n📝 {len(nicknames)} active nicknames",
                    inline=True
                )
            except Exception as e:
                embed.add_field(
                    name="📊 Database Status", 
                    value="❌ Error accessing database",
                    inline=True
                )
        else:
            embed.add_field(
                name="📊 Database Status",
                value="❌ Not connected",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        bot.logger.error(f"Error in status command: {e}")
        await interaction.response.send_message("Error retrieving status.", ephemeral=True)

@bot.tree.command(name="restore", description="Manually restore a user's nickname (owner only)")
@app_commands.describe(member="The member whose nickname to restore (leave empty for yourself)")
async def restore_command(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Manually restore a user's nickname."""
    try:
        # Check if user is guild owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can use this command.", ephemeral=True)
            return
        # Default to the user who ran the command
        target_member = member or interaction.user
        
        # Ensure target_member is a Member object (not User)
        if not isinstance(target_member, discord.Member):
            target_member = interaction.guild.get_member(target_member.id)
        
        if not target_member:
            await interaction.response.send_message("Member not found in this server.", ephemeral=True)
            return
        
        # Check if we have their original nickname stored
        if target_member.id in bot.original_nicknames:
            original_nick = bot.original_nicknames[target_member.id]
            
            # Restore nickname
            if original_nick != target_member.name:
                await target_member.edit(nick=original_nick)
            else:
                await target_member.edit(nick=None)
            
            # Clean up storage
            del bot.original_nicknames[target_member.id]
            
            await interaction.response.send_message(
                f"✅ Restored {target_member.mention}'s nickname to `{original_nick}`",
                ephemeral=True
            )
            bot.logger.info(f"Manually restored {target_member.name}'s nickname")
        else:
            await interaction.response.send_message(
                f"❌ No stored nickname found for {target_member.mention}",
                ephemeral=True
            )
    
    except discord.Forbidden:
        await interaction.response.send_message("❌ No permission to change nicknames.", ephemeral=True)
    except Exception as e:
        bot.logger.error(f"Error in restore command: {e}")
        await interaction.response.send_message("❌ Error restoring nickname.", ephemeral=True)

@bot.tree.command(name="add_nickname", description="Add a new nickname to the server (owner only)")
@app_commands.describe(nickname="The nickname to add (will be formatted as 'Nickname 001')")
async def add_nickname_command(interaction: discord.Interaction, nickname: str):
    """Add a new nickname to the guild's database."""
    try:
        if not bot.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        # Check if user is guild owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can use this command.", ephemeral=True)
            return
        
        # Add nickname to database
        result = bot.db.add_nickname(interaction.guild.id, nickname, interaction.user.id)
        
        if result:
            await interaction.response.send_message(f"✅ Added nickname: `{result.nickname}`", ephemeral=True)
            bot.logger.info(f"Added nickname '{result.nickname}' to guild {interaction.guild.name}")
        else:
            await interaction.response.send_message(f"❌ Nickname `{nickname}` already exists.", ephemeral=True)
    
    except Exception as e:
        bot.logger.error(f"Error adding nickname: {e}")
        await interaction.response.send_message("❌ Error adding nickname.", ephemeral=True)

@bot.tree.command(name="remove_nickname", description="Remove a nickname from the server (owner only)")
@app_commands.describe(nickname="The nickname to remove")
async def remove_nickname_command(interaction: discord.Interaction, nickname: str):
    """Remove a nickname from the guild's database (owner only)."""
    try:
        if not bot.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        # Check if user is guild owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can remove nicknames.", ephemeral=True)
            return
        
        # Remove nickname from database
        success, message = bot.db.remove_nickname(interaction.guild.id, nickname, interaction.user.id)
        
        if success:
            await interaction.response.send_message(f"✅ {message}", ephemeral=True)
            bot.logger.info(f"Removed nickname '{nickname}' from guild {interaction.guild.name}")
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    except Exception as e:
        bot.logger.error(f"Error removing nickname: {e}")
        await interaction.response.send_message("❌ Error removing nickname.", ephemeral=True)

@bot.tree.command(name="list_nicknames", description="List all active nicknames for this server (owner only)")
async def list_nicknames_command(interaction: discord.Interaction):
    """List all active nicknames for this guild."""
    try:
        # Check if user is guild owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can use this command.", ephemeral=True)
            return
            
        if not bot.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        nicknames = bot.db.get_guild_nicknames(interaction.guild.id)
        
        if not nicknames:
            await interaction.response.send_message("📝 No nicknames configured for this server.", ephemeral=True)
            return
        
        # Create embed with nickname list
        embed = discord.Embed(
            title=f"📝 Nicknames for {interaction.guild.name}",
            description=f"Total: {len(nicknames)} active nicknames",
            color=discord.Color.blue()
        )
        
        # Group nicknames in chunks for display
        nickname_list = []
        for i, nick in enumerate(nicknames[:20], 1):  # Limit to 20
            nickname_list.append(f"{i}. {nick.nickname}")
        
        embed.add_field(
            name="Active Nicknames",
            value="\n".join(nickname_list) if nickname_list else "None",
            inline=False
        )
        
        if len(nicknames) > 20:
            embed.set_footer(text=f"Showing first 20 of {len(nicknames)} nicknames")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    except Exception as e:
        bot.logger.error(f"Error listing nicknames: {e}")
        await interaction.response.send_message("❌ Error retrieving nicknames.", ephemeral=True)

@bot.tree.command(name="bot_health", description="Comprehensive bot status check (owner only)")
async def bot_health_command(interaction: discord.Interaction):
    """Comprehensive bot status check (owner only)."""
    try:
        # Check if user is guild owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can check bot health.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏥 Bot Health Check",
            color=discord.Color.blue()
        )
        
        # Bot status
        embed.add_field(
            name="🤖 Bot Status",
            value=f"✅ Online\n🏠 {len(bot.guilds)} servers\n👥 {len(bot.original_nicknames)} tracked users",
            inline=True
        )
        
        # Database status
        if bot.db:
            try:
                nicknames = bot.db.get_guild_nicknames(interaction.guild.id)
                embed.add_field(
                    name="💾 Database",
                    value=f"✅ Connected\n📝 {len(nicknames)} nicknames",
                    inline=True
                )
            except Exception as e:
                embed.add_field(
                    name="💾 Database",
                    value=f"❌ Error: {str(e)[:50]}...",
                    inline=True
                )
        else:
            embed.add_field(
                name="💾 Database",
                value="❌ Not connected",
                inline=True
            )
        
        # Voice channel monitoring
        voice_users = []
        for guild in bot.guilds:
            for member in guild.members:
                if member.voice and member.voice.channel:
                    voice_users.append(member)
        
        embed.add_field(
            name="🎤 Voice Monitoring",
            value=f"👥 {len(voice_users)} users in voice\n🔊 Monitoring active",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    except Exception as e:
        bot.logger.error(f"Error in bot health command: {e}")
        await interaction.response.send_message("❌ Error checking bot health.", ephemeral=True)