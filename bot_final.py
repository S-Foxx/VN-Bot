"""
Discord Voice Channel Nickname Bot with Slash Commands
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
        """Called when the bot starts - register and sync slash commands."""
        try:
            # Add all slash commands to the tree
            self.tree.add_command(self.status_command)
            self.tree.add_command(self.restore_command) 
            self.tree.add_command(self.add_nickname_command)
            self.tree.add_command(self.remove_nickname_command)
            self.tree.add_command(self.list_nicknames_command)
            
            # Sync commands with Discord
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
                    self.db.ensure_guild_exists(guild.id, guild.name, guild.owner_id)
                    self.logger.info(f"Registered guild: {guild.name} (ID: {guild.id})")
                except Exception as e:
                    self.logger.error(f"Failed to register guild {guild.name}: {e}")

    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        if self.db:
            try:
                self.db.ensure_guild_exists(guild.id, guild.name, guild.owner_id)
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

    @app_commands.command(name="status", description="Display bot status and tracked users")
    async def status_command(self, interaction: discord.Interaction):
        """Display bot status and tracked users."""
        try:
            embed = discord.Embed(
                title="🤖 Voice Nickname Bot Status",
                description=f"Currently active in **{interaction.guild.name}**",
                color=discord.Color.green()
            )
            
            # Show tracked users
            if self.original_nicknames:
                tracked_users = []
                for user_id in self.original_nicknames:
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
            if self.db:
                try:
                    nicknames = self.db.get_guild_nicknames(interaction.guild.id)
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
            self.logger.error(f"Error in status command: {e}")
            await interaction.response.send_message("Error retrieving status.", ephemeral=True)

    @app_commands.command(name="restore", description="Manually restore a user's nickname")
    @app_commands.describe(member="The member whose nickname to restore (leave empty for yourself)")
    async def restore_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Manually restore a user's nickname."""
        try:
            # Default to the user who ran the command
            target_member = member or interaction.user
            
            # Ensure target_member is a Member object (not User)
            if not isinstance(target_member, discord.Member):
                target_member = interaction.guild.get_member(target_member.id)
            
            if not target_member:
                await interaction.response.send_message("Member not found in this server.", ephemeral=True)
                return
            
            # Check if we have their original nickname stored
            if target_member.id in self.original_nicknames:
                original_nick = self.original_nicknames[target_member.id]
                
                # Restore nickname
                if original_nick != target_member.name:
                    await target_member.edit(nick=original_nick)
                else:
                    await target_member.edit(nick=None)
                
                # Clean up storage
                del self.original_nicknames[target_member.id]
                
                await interaction.response.send_message(
                    f"✅ Restored {target_member.mention}'s nickname to `{original_nick}`",
                    ephemeral=True
                )
                self.logger.info(f"Manually restored {target_member.name}'s nickname")
            else:
                await interaction.response.send_message(
                    f"❌ No stored nickname found for {target_member.mention}",
                    ephemeral=True
                )
        
        except discord.Forbidden:
            await interaction.response.send_message("❌ No permission to change nicknames.", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error in restore command: {e}")
            await interaction.response.send_message("❌ Error restoring nickname.", ephemeral=True)

    @app_commands.command(name="add_nickname", description="Add a new nickname to the server")
    @app_commands.describe(nickname="The nickname to add (will be formatted as 'Nickname 001')")
    async def add_nickname_command(self, interaction: discord.Interaction, nickname: str):
        """Add a new nickname to the guild's database."""
        try:
            if not self.db:
                await interaction.response.send_message("❌ Database not available.", ephemeral=True)
                return
            
            # Check permissions (anyone can add nicknames)
            if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_nicknames:
                await interaction.response.send_message("❌ You need 'Manage Nicknames' permission to add nicknames.", ephemeral=True)
                return
            
            # Add nickname to database
            result = self.db.add_nickname(interaction.guild.id, nickname, interaction.user.id)
            
            if result:
                await interaction.response.send_message(f"✅ Added nickname: `{result.nickname}`", ephemeral=True)
                self.logger.info(f"Added nickname '{result.nickname}' to guild {interaction.guild.name}")
            else:
                await interaction.response.send_message(f"❌ Nickname `{nickname}` already exists.", ephemeral=True)
        
        except Exception as e:
            self.logger.error(f"Error adding nickname: {e}")
            await interaction.response.send_message("❌ Error adding nickname.", ephemeral=True)

    @app_commands.command(name="remove_nickname", description="Remove a nickname from the server (owner only)")
    @app_commands.describe(nickname="The nickname to remove")
    async def remove_nickname_command(self, interaction: discord.Interaction, nickname: str):
        """Remove a nickname from the guild's database (owner only)."""
        try:
            if not self.db:
                await interaction.response.send_message("❌ Database not available.", ephemeral=True)
                return
            
            # Check if user is guild owner
            if interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message("❌ Only the server owner can remove nicknames.", ephemeral=True)
                return
            
            # Remove nickname from database
            success, message = self.db.remove_nickname(interaction.guild.id, nickname, interaction.user.id)
            
            if success:
                await interaction.response.send_message(f"✅ {message}", ephemeral=True)
                self.logger.info(f"Removed nickname '{nickname}' from guild {interaction.guild.name}")
            else:
                await interaction.response.send_message(f"❌ {message}", ephemeral=True)
        
        except Exception as e:
            self.logger.error(f"Error removing nickname: {e}")
            await interaction.response.send_message("❌ Error removing nickname.", ephemeral=True)

    @app_commands.command(name="list_nicknames", description="List all active nicknames for this server")
    async def list_nicknames_command(self, interaction: discord.Interaction):
        """List all active nicknames for this guild."""
        try:
            if not self.db:
                await interaction.response.send_message("❌ Database not available.", ephemeral=True)
                return
            
            nicknames = self.db.get_guild_nicknames(interaction.guild.id)
            
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
            self.logger.error(f"Error listing nicknames: {e}")
            await interaction.response.send_message("❌ Error retrieving nicknames.", ephemeral=True)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle slash command errors."""
        self.logger.error(f"Slash command error: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)