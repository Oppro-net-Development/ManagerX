import discord
from discord.ext import commands
from discord import option, slash_command, SlashCommandGroup
import ezcord
import sqlite3
import os
from typing import Optional, Tuple

# OWN IMPORT
from ui.emojis import emoji_yes, emoji_no, emoji_settings
from ui.colors import INFO_COLOR


# Database handling
class TempVCDatabase:
    def __init__(self, db_path: str = "data/tempvc.db"):
        self.db_path = db_path
        # Erstelle das data Verzeichnis falls es nicht existiert
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tempvc_settings (
                guild_id INTEGER PRIMARY KEY,
                creator_channel_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                auto_delete_time INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_channels (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def set_tempvc_settings(self, guild_id: int, creator_channel_id: int, category_id: int, auto_delete_time: int = 0):
        """Set or update temp VC settings for a guild"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tempvc_settings 
            (guild_id, creator_channel_id, category_id, auto_delete_time) 
            VALUES (?, ?, ?, ?)
        ''', (guild_id, creator_channel_id, category_id, auto_delete_time))
        conn.commit()
        conn.close()

    def get_tempvc_settings(self, guild_id: int) -> Optional[Tuple[int, int, int]]:
        """Get temp VC settings for a guild"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT creator_channel_id, category_id, auto_delete_time 
            FROM tempvc_settings 
            WHERE guild_id = ?
        ''', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def remove_tempvc_settings(self, guild_id: int):
        """Remove temp VC settings for a guild"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tempvc_settings WHERE guild_id = ?', (guild_id,))
        # Entferne auch alle temp channels dieser guild
        cursor.execute('DELETE FROM temp_channels WHERE guild_id = ?', (guild_id,))
        conn.commit()
        conn.close()

    def add_temp_channel(self, channel_id: int, guild_id: int, owner_id: int):
        """Add a temp channel to tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO temp_channels (channel_id, guild_id, owner_id) 
            VALUES (?, ?, ?)
        ''', (channel_id, guild_id, owner_id))
        conn.commit()
        conn.close()

    def remove_temp_channel(self, channel_id: int):
        """Remove a temp channel from tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM temp_channels WHERE channel_id = ?', (channel_id,))
        conn.commit()
        conn.close()

    def is_temp_channel(self, channel_id: int) -> bool:
        """Check if a channel is a tracked temp channel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM temp_channels WHERE channel_id = ?', (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_temp_channel_owner(self, channel_id: int) -> Optional[int]:
        """Get the owner of a temp channel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT owner_id FROM temp_channels WHERE channel_id = ?', (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_all_temp_channels(self, guild_id: int) -> list:
        """Get all temp channels for a guild"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT channel_id, owner_id, created_at 
            FROM temp_channels 
            WHERE guild_id = ?
        ''', (guild_id,))
        result = cursor.fetchall()
        conn.close()
        return result

    def update_channel_activity(self, channel_id: int):
        """Update last activity timestamp for a channel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE temp_channels 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE channel_id = ?
        ''', (channel_id,))
        conn.commit()
        conn.close()

    def get_channels_to_delete(self, guild_id: int, minutes_inactive: int) -> list:
        """Get channels that should be deleted based on inactivity"""
        if minutes_inactive <= 0:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT channel_id FROM temp_channels 
            WHERE guild_id = ? 
            AND datetime(last_activity, '+{} minutes') < datetime('now')
        '''.format(minutes_inactive), (guild_id,))
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result


# Initialize database
db = TempVCDatabase()


class TempVC(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    tempvc = SlashCommandGroup("tempvc", "Temp-VC Management")

    @tempvc.command(name="create", description="Erstelle ein VC-Erstellungssystem")
    @option("creator_channel", description="Channel, den Mitglieder betreten, um ihren VC zu erstellen",
            channel_types=[discord.ChannelType.voice])
    @option("category", description="Kategorie, in der die Temp-Channels erstellt werden",
            channel_types=[discord.ChannelType.category])
    async def tempvc_create(self, ctx: discord.ApplicationContext, creator_channel: discord.VoiceChannel,
                            category: discord.CategoryChannel):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("Du brauchst Administratorrechte.", ephemeral=True)

        try:
            db.set_tempvc_settings(ctx.guild.id, creator_channel.id, category.id)
            await ctx.respond(
                f"{emoji_yes} Temp-VC System aktiviert!\n"
                f"Ersteller-Channel: **{creator_channel.name}**\n"
                f"Kategorie: **{category.name}**",
                ephemeral=True
            )
        except Exception as e:
            await ctx.respond(f"{emoji_no} Fehler beim Erstellen des Systems: {str(e)}", ephemeral=True)

    @tempvc.command(name="remove", description="Entferne das VC-Erstellungssystem")
    async def tempvc_remove(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("Du brauchst Administratorrechte.", ephemeral=True)

        try:
            settings = db.get_tempvc_settings(ctx.guild.id)
            if not settings:
                return await ctx.respond(f"{emoji_no} Kein Temp-VC System aktiv.", ephemeral=True)

            # Remove settings from database
            db.remove_tempvc_settings(ctx.guild.id)

            await ctx.respond(f"{emoji_yes} Temp-VC System deaktiviert!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"{emoji_no} Fehler beim Entfernen des Systems: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            # Handle joining creator channel
            if after.channel:
                await self.handle_creator_channel_join(member, after.channel)

            # Handle leaving channels (cleanup empty temp channels)
            if before.channel:
                await self.handle_channel_leave(before.channel)

        except Exception as e:
            print(f"Error in voice state update: {e}")

    async def handle_creator_channel_join(self, member: discord.Member, channel: discord.VoiceChannel):
        """Handle when a member joins the creator channel"""
        settings = db.get_tempvc_settings(member.guild.id)
        if not settings:
            return

        # Fix: Unpack all 3 values returned by get_tempvc_settings
        creator_channel_id, category_id, auto_delete_time = settings

        # Check if user joined the creator channel
        if channel.id != creator_channel_id:
            return

        guild = member.guild
        category = discord.utils.get(guild.categories, id=category_id)

        if not category:
            print(f"Category with ID {category_id} not found in guild {guild.id}")
            return

        # Create permission overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                manage_permissions=True
            )
        }

        try:
            # Create the temporary voice channel
            temp_channel = await guild.create_voice_channel(
                name=f"🔊 {member.display_name}'s Raum",
                category=category,
                overwrites=overwrites
            )

            # Add to database tracking
            db.add_temp_channel(temp_channel.id, guild.id, member.id)

            # Move user to the new channel
            await member.move_to(temp_channel)

        except discord.Forbidden:
            print(f"Missing permissions to create voice channel in guild {guild.id}")
        except discord.HTTPException as e:
            print(f"HTTP error when creating voice channel: {e}")
        except Exception as e:
            print(f"Unexpected error when creating temp channel: {e}")

    async def handle_channel_leave(self, channel: discord.VoiceChannel):
        """Handle cleanup when channels become empty"""
        # Only process if channel is empty
        if len(channel.members) > 0:
            return

        # Check if this is a tracked temp channel
        if not db.is_temp_channel(channel.id):
            return

        try:
            # Remove from database first
            db.remove_temp_channel(channel.id)

            # Delete the channel
            await channel.delete(reason="Temp channel cleanup - channel empty")

        except discord.Forbidden:
            print(f"Missing permissions to delete channel {channel.id}")
        except discord.NotFound:
            # Channel already deleted, just remove from database
            db.remove_temp_channel(channel.id)
        except Exception as e:
            print(f"Error deleting temp channel {channel.id}: {e}")

    @tempvc.command(name="settings", description="Zeige die aktuellen Temp-VC Einstellungen")
    async def tempvc_settings(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("Du brauchst Administratorrechte.", ephemeral=True)

        settings = db.get_tempvc_settings(ctx.guild.id)
        if not settings:
            return await ctx.respond(f"{emoji_no} Kein Temp-VC System aktiv.", ephemeral=True)

        # Fix: Unpack all 3 values returned by get_tempvc_settings
        creator_channel_id, category_id, auto_delete_time = settings
        creator_channel = ctx.guild.get_channel(creator_channel_id)
        category = ctx.guild.get_channel(category_id)

        embed = discord.Embed(
            title=f"{emoji_settings} Temp-VC Einstellungen",
            color={INFO_COLOR}
        )
        embed.add_field(
            name="Ersteller-Channel",
            value=creator_channel.mention if creator_channel else f"{emoji_no} Channel nicht gefunden (ID: {creator_channel_id})",
            inline=False
        )
        embed.add_field(
            name="Kategorie",
            value=category.name if category else f"{emoji_no} Kategorie nicht gefunden (ID: {category_id})",
            inline=False
        )
        embed.add_field(
            name="Auto-Delete Zeit",
            value=f"{auto_delete_time} Minuten" if auto_delete_time > 0 else "Deaktiviert",
            inline=False
        )

        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(TempVC(bot))