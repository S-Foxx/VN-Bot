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
        intents.message_content = True  # Required for commands to work properly
        
        super().__init__(
            command_prefix=BOT_CONFIG['command_prefix'],
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
        """Called during bot setup to add commands to the tree."""
        # Create and add slash commands
        @app_commands.command(name="status", description="Display bot status and tracked users")
        async def status(interaction: discord.Interaction):
            await self.status_command(interaction)
        
        @app_commands.command(name="restore", description="Manually restore a user's nickname")
        @app_commands.describe(member="The member whose nickname to restore (leave empty for yourself)")
        async def restore(interaction: discord.Interaction, member: Optional[discord.Member] = None):
            await self.restore_command(interaction, member)
        
        @app_commands.command(name="add_nickname", description="Add a new nickname to the server")
        @app_commands.describe(nickname="The nickname to add (will be formatted as 'Nickname 001')")
        async def add_nickname(interaction: discord.Interaction, nickname: str):
            await self.add_nickname_command(interaction, nickname)
        
        @app_commands.command(name="remove_nickname", description="Remove a nickname from the server (owner only)")
        @app_commands.describe(nickname="The nickname to remove")
        async def remove_nickname(interaction: discord.Interaction, nickname: str):
            await self.remove_nickname_command(interaction, nickname)
        
        @app_commands.command(name="list_nicknames", description="List all active nicknames for this server")
        async def list_nicknames(interaction: discord.Interaction):
            await self.list_nicknames_command(interaction)
        
        @app_commands.command(name="find_nickname", description="Search for a specific nickname (owner only)")
        @app_commands.describe(search_term="The nickname to search for")
        async def find_nickname(interaction: discord.Interaction, search_term: str):
            await self.find_nickname_command(interaction, search_term)
        
        @app_commands.command(name="bot_health", description="Comprehensive bot status check (owner only)")
        async def bot_health(interaction: discord.Interaction):
            await self.bot_status_command(interaction)
        
        # Add commands to tree
        self.tree.add_command(status)
        self.tree.add_command(restore)
        self.tree.add_command(add_nickname)
        self.tree.add_command(remove_nickname)
        self.tree.add_command(list_nicknames)
        self.tree.add_command(find_nickname)
        self.tree.add_command(bot_health)
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Register all guilds in database
        if self.db:
            for guild in self.guilds:
                try:
                    self.db.ensure_guild_exists(guild.id, guild.name, guild.owner_id or 0)
                    self.logger.info(f"Registered guild: {guild.name} (ID: {guild.id})")
                except Exception as e:
                    self.logger.error(f"Failed to register guild {guild.name}: {e}")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="voice channels"
            )
        )
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Register the new guild in database
        if self.db:
            try:
                self.db.ensure_guild_exists(guild.id, guild.name, guild.owner_id or 0)
                self.logger.info(f"Registered new guild: {guild.name}")
            except Exception as e:
                self.logger.error(f"Failed to register new guild {guild.name}: {e}")
    
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Handle voice state changes (join/leave voice channels).
        
        Args:
            member: The member whose voice state changed
            before: Voice state before the change
            after: Voice state after the change
        """
        # Skip if it's the bot itself
        if member.bot:
            return
        
        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            await self.handle_voice_join(member)
        
        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            await self.handle_voice_leave(member)
    
    async def handle_voice_join(self, member: discord.Member):
        """
        Handle when a user joins a voice channel.
        
        Args:
            member: The member who joined the voice channel
        """
        user_id = member.id
        original_nickname = member.display_name
        
        # Skip if already tracking this user
        if user_id in self.original_nicknames:
            return
        
        # Store original nickname
        self.original_nicknames[user_id] = original_nickname
        self.logger.info(f"{member.display_name} joined voice channel: {member.voice.channel.name}")
        self.logger.info(f"Stored original nickname for {member.name}: '{original_nickname}'")
        
        # Generate and assign new nickname
        new_nickname = self.generate_nickname(member.guild.id)
        if new_nickname:
            try:
                await member.edit(nick=new_nickname)
                self.logger.info(f"Changed {member.name}'s nickname to '{new_nickname}'")
            except discord.Forbidden:
                self.logger.warning(f"No permission to change {member.name}'s nickname")
            except Exception as e:
                self.logger.error(f"Error changing {member.name}'s nickname: {e}")
    
    async def handle_voice_leave(self, member: discord.Member):
        """
        Handle when a user leaves a voice channel.
        
        Args:
            member: The member who left the voice channel
        """
        user_id = member.id
        
        # Skip if not tracking this user
        if user_id not in self.original_nicknames:
            return
        
        # Restore original nickname
        original_nickname = self.original_nicknames.pop(user_id)
        
        try:
            await member.edit(nick=original_nickname if original_nickname != member.name else None)
            self.logger.info(f"Restored {member.name}'s nickname to '{original_nickname}'")
        except discord.Forbidden:
            self.logger.warning(f"No permission to restore {member.name}'s nickname")
        except Exception as e:
            self.logger.error(f"Error restoring {member.name}'s nickname: {e}")
    
    def generate_nickname(self, guild_id: int) -> Optional[str]:
        """
        Generate a random nickname from the database for the specified guild.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            A randomly selected nickname string with 3-digit counter, or None if no nicknames available
        """
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

    # Command implementations
    async def status_command(self, interaction: discord.Interaction):
        """Display bot status and tracked users."""
        try:
            embed = discord.Embed(
                title="🤖 Voice Nickname Bot Status",
                description=f"Currently active in **{interaction.guild.name}**",
                color=discord.Color.green()
            )
            
            # Show tracked users
            tracked_count = len(self.original_nicknames)
            embed.add_field(
                name="📊 Activity",
                value=f"Tracking {tracked_count} users in voice channels",
                inline=False
            )
            
            # Database status
            if self.db:
                try:
                    nicknames = self.db.get_guild_nicknames(interaction.guild.id)
                    nickname_count = len(nicknames)
                    embed.add_field(
                        name="💾 Database",
                        value=f"✅ Connected • {nickname_count} nicknames available",
                        inline=False
                    )
                except:
                    embed.add_field(
                        name="💾 Database", 
                        value="⚠️ Connection issues",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="💾 Database",
                    value="❌ Not available (using fallback nicknames)",
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ How it works",
                value="Join a voice channel to get a temporary nickname!\nLeave to restore your original name.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in status command: {e}")
            await interaction.response.send_message("❌ An error occurred while getting status information.", ephemeral=True)

    @app_commands.command(name="restore", description="Manually restore a user's nickname")
    @app_commands.describe(member="The member whose nickname to restore (leave empty for yourself)")
    async def restore_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Manually restore a user's nickname."""
        if member is None:
            member = interaction.user
        
        user_id = member.id
        if user_id in self.original_nicknames:
            original_nickname = self.original_nicknames.pop(user_id)
            try:
                await member.edit(nick=original_nickname if original_nickname != member.name else None)
                await interaction.response.send_message(f"✅ Restored {member.mention}'s nickname to '{original_nickname}'")
                self.logger.info(f"Manually restored {member.name}'s nickname to '{original_nickname}'")
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to change that user's nickname.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error restoring nickname: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {member.mention} is not currently being tracked.", ephemeral=True)
    
    @app_commands.command(name="add_nickname", description="Add a new nickname to the server")
    @app_commands.describe(nickname="The nickname to add (will be formatted as 'Nickname 001')")
    async def add_nickname_command(self, interaction: discord.Interaction, nickname: str):
        """Add a new nickname to the guild's database."""
        if not self.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.manage_nicknames:
            await interaction.response.send_message("❌ You need 'Manage Nicknames' permission to use this command.", ephemeral=True)
            return
        
        try:
            result = self.db.add_nickname(interaction.guild.id, nickname, interaction.user.id)
            if result:
                await interaction.response.send_message(f"✅ Added nickname: **{result.nickname}**")
                self.logger.info(f"Added nickname '{result.nickname}' to guild {interaction.guild.name} by {interaction.user}")
            else:
                await interaction.response.send_message(f"❌ Nickname **{nickname.strip()}** already exists or is invalid.", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error adding nickname: {e}")
            await interaction.response.send_message("❌ An error occurred while adding the nickname.", ephemeral=True)
    
    @app_commands.command(name="remove_nickname", description="Remove a nickname from the server (owner only)")
    @app_commands.describe(nickname="The nickname to remove")
    async def remove_nickname_command(self, interaction: discord.Interaction, nickname: str):
        """Remove a nickname from the guild's database (owner only)."""
        if not self.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        try:
            success, message = self.db.remove_nickname(interaction.guild.id, nickname, interaction.user.id)
            if success:
                await interaction.response.send_message(f"✅ {message}")
                self.logger.info(f"Removed nickname '{nickname.strip()}' from guild {interaction.guild.name} by {interaction.user}")
            else:
                await interaction.response.send_message(f"❌ {message}", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error removing nickname: {e}")
            await interaction.response.send_message("❌ An error occurred while removing the nickname.", ephemeral=True)
    
    @app_commands.command(name="list_nicknames", description="List all active nicknames for this server")
    async def list_nicknames_command(self, interaction: discord.Interaction):
        """List all active nicknames for this guild."""
        if not self.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        try:
            nicknames = self.db.get_guild_nicknames(interaction.guild.id)
            if not nicknames:
                embed = discord.Embed(
                    title="📝 Nickname Database",
                    description="No nicknames configured for this server.\nUse `/add_nickname` to add some!",
                    color=discord.Color.orange()
                )
            else:
                # Format nicknames in a nice list
                nickname_list = []
                for i, nick in enumerate(nicknames, 1):
                    nickname_list.append(f"`{i:2d}.` **{nick.nickname}**")
                
                # Split into multiple embeds if too many nicknames
                max_per_embed = 20
                if len(nickname_list) <= max_per_embed:
                    embed = discord.Embed(
                        title=f"📝 Nickname Database ({len(nicknames)} total)",
                        description="\n".join(nickname_list),
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="ℹ️ Usage",
                        value="Nicknames are randomly selected and formatted as: `Nickname 001`",
                        inline=False
                    )
                else:
                    # Show first 20 with note about more
                    embed = discord.Embed(
                        title=f"📝 Nickname Database ({len(nicknames)} total)",
                        description="\n".join(nickname_list[:max_per_embed]) + f"\n\n*...and {len(nicknames) - max_per_embed} more*",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="ℹ️ Usage",
                        value="Nicknames are randomly selected and formatted as: `Nickname 001`",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
                    
        except Exception as e:
            self.logger.error(f"Error listing nicknames: {e}")
            await interaction.response.send_message("❌ An error occurred while listing nicknames.", ephemeral=True)
    
    @app_commands.command(name="find_nickname", description="Search for a specific nickname (owner only)")
    @app_commands.describe(search_term="The nickname to search for")
    async def find_nickname_command(self, interaction: discord.Interaction, search_term: str):
        """Find a specific nickname in the guild's database (owner only)."""
        if not self.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        # Only allow server owners to search (to prevent spam)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can search nicknames.", ephemeral=True)
            return
        
        try:
            nicknames = self.db.get_guild_nicknames(interaction.guild.id)
            search_lower = search_term.lower().strip()
            
            # Find matching nicknames (case-insensitive partial match)
            matches = [nick for nick in nicknames if search_lower in nick.nickname.lower()]
            
            if not matches:
                embed = discord.Embed(
                    title="🔍 Search Results",
                    description=f"No nicknames found containing: **{search_term}**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Try a shorter search term or check `/list_nicknames` to see all available nicknames.",
                    inline=False
                )
            else:
                # Format matches
                match_list = []
                for i, nick in enumerate(matches, 1):
                    match_list.append(f"`{i}.` **{nick.nickname}**")
                
                embed = discord.Embed(
                    title="🔍 Search Results",
                    description=f"Found {len(matches)} nickname(s) containing: **{search_term}**\n\n" + "\n".join(match_list),
                    color=discord.Color.green()
                )
                
                if len(matches) == 1:
                    embed.add_field(
                        name="ℹ️ Format",
                        value=f"In voice channels, this appears as: `{matches[0].nickname} 001`",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error searching nicknames: {e}")
            await interaction.response.send_message("❌ An error occurred while searching nicknames.", ephemeral=True)
    
    @app_commands.command(name="bot_health", description="Comprehensive bot status check (owner only)")
    async def bot_status_command(self, interaction: discord.Interaction):
        """Comprehensive bot status check (owner only)."""
        # Only allow server owners to see detailed status
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can check bot status.", ephemeral=True)
            return
        
        try:
            # Database status
            db_status = "✅ Connected" if self.db else "❌ Disconnected"
            nickname_count = 0
            
            if self.db:
                try:
                    nicknames = self.db.get_guild_nicknames(interaction.guild.id)
                    nickname_count = len(nicknames)
                except:
                    db_status = "⚠️ Connection Issues"
            
            # Voice tracking status
            tracked_users = len(self.original_nicknames)
            
            # Bot permissions check
            bot_member = interaction.guild.get_member(self.user.id)
            can_manage_nicknames = bot_member.guild_permissions.manage_nicknames if bot_member else False
            
            # Create status embed
            embed = discord.Embed(
                title="🤖 Bot Health Report",
                description=f"Status report for **{interaction.guild.name}**",
                color=discord.Color.blue()
            )
            
            # Database section
            embed.add_field(
                name="💾 Database",
                value=f"**Status:** {db_status}\n**Nicknames:** {nickname_count} configured",
                inline=True
            )
            
            # Voice tracking section
            embed.add_field(
                name="🎤 Voice Tracking",
                value=f"**Active:** {tracked_users} users\n**Feature:** {'✅ Working' if tracked_users >= 0 else '❌ Error'}",
                inline=True
            )
            
            # Permissions section
            perm_status = "✅ Proper" if can_manage_nicknames else "❌ Missing"
            embed.add_field(
                name="🔐 Permissions",
                value=f"**Manage Nicknames:** {perm_status}\n**Required:** Manage Nicknames",
                inline=True
            )
            
            # Overall health
            overall_health = "✅ Healthy"
            if not self.db:
                overall_health = "⚠️ Limited (No Database)"
            elif not can_manage_nicknames:
                overall_health = "❌ Impaired (No Permissions)"
            elif db_status == "⚠️ Connection Issues":
                overall_health = "⚠️ Degraded (DB Issues)"
            
            embed.add_field(
                name="📊 Overall Health",
                value=overall_health,
                inline=False
            )
            
            # Add tips based on status
            tips = []
            if not can_manage_nicknames:
                tips.append("• Grant the bot 'Manage Nicknames' permission")
            if nickname_count == 0 and self.db:
                tips.append("• Add nicknames with `/add_nickname`")
            if not self.db:
                tips.append("• Database features unavailable (using fallback)")
            
            if tips:
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(tips),
                    inline=False
                )
            
            embed.set_footer(text=f"Bot uptime: Since last restart • Server: {interaction.guild.name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error checking bot status: {e}")
            await interaction.response.send_message("❌ An error occurred while checking bot status.", ephemeral=True)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle slash command errors."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            self.logger.error(f"Slash command error: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)