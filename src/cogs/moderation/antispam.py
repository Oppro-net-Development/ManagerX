# Copyright (c) 2025 OPPRO.NET Network
from collections import defaultdict
import asyncio
import discord
from discord import SlashCommandGroup
import ezcord
import datetime
from datetime import timedelta


from DevTools.ui import (
    emoji_yes,
    emoji_no,
    emoji_forbidden,
    emoji_warn,
    emoji_delete,
    emoji_member,
    emoji_channel,
    emoji_moderator,
    emoji_add,
    emoji_statistics,
    emoji_annoattention,
    emoji_owner,
)

from DevTools import SpamDB


class AntiSpam(ezcord.Cog):
    antispam = SlashCommandGroup(
        "antispam",
        "Verwalte Anti-Spam-Einstellungen und Protokolle.",
    )

    def __init__(self, bot: ezcord.Bot):
        self.bot = bot
        self.db = SpamDB()
        # Track user message timestamps per guild
        self.user_messages = defaultdict(lambda: defaultdict(list))
        # Track users currently in timeout to prevent duplicate actions
        self.users_in_timeout = set()

    @ezcord.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for spam detection."""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return

        # Check if user is whitelisted
        if self.is_whitelisted(message.guild.id, message.author.id):
            return

        # Get spam settings for this guild
        settings = self.db.get_spam_settings(message.guild.id)
        if not settings:
            # If no settings are configured, don't process spam detection
            return

        # Check if log channel is set
        if not settings.get('log_channel_id'):
            return

        # Record this message timestamp
        user_id = message.author.id
        guild_id = message.guild.id
        current_time = datetime.now()

        # Add current message to tracking
        self.user_messages[guild_id][user_id].append(current_time)

        # Clean old messages outside the time frame
        time_threshold = current_time - timedelta(seconds=settings['time_frame'])
        self.user_messages[guild_id][user_id] = [
            timestamp for timestamp in self.user_messages[guild_id][user_id]
            if timestamp > time_threshold
        ]

        # Check if user exceeded message limit
        message_count = len(self.user_messages[guild_id][user_id])
        if message_count > settings['max_messages']:
            await self.handle_spam_violation(message, settings)

    async def handle_spam_violation(self, message, settings):
        """Handle a user who violated spam limits."""
        user = message.author
        guild = message.guild

        # Prevent duplicate actions for the same user
        user_timeout_key = f"{guild.id}_{user.id}"
        if user_timeout_key in self.users_in_timeout:
            return

        self.users_in_timeout.add(user_timeout_key)

        try:
            # Log the spam incident
            self.db.log_spam(guild.id, user.id, message.content[:100])  # Limit message length

            # Delete recent messages from this user
            await self.delete_recent_messages(message.channel, user, limit=settings['max_messages'])

            # Apply timeout (5 minutes)
            timeout_duration = timedelta(minutes=5)
            timeout_applied = False

            try:
                await user.timeout_for(timeout_duration, reason="Anti-Spam: Zu viele Nachrichten")
                timeout_applied = True
            except discord.Forbidden:
                pass  # Continue to log even if timeout fails

            # Send log to designated channel
            await self.send_spam_log(guild, user, message, settings, timeout_applied)

            # Send warning message in channel
            embed = discord.Embed(
                title=f"{emoji_forbidden} × Anti-Spam Warnung",
                description=f"{user.mention} wurde wegen zu vieler Nachrichten {'stumm geschaltet' if timeout_applied else 'verwarnt'}.",
                color=ERROR_COLOR
            )
            embed.add_field(
                name="Limit überschritten",
                value=f"Maximal {settings['max_messages']} Nachrichten in {settings['time_frame']} Sekunden erlaubt",
                inline=False
            )
            await message.channel.send(embed=embed, delete_after=10)

            # Clear user's message tracking after violation
            if guild.id in self.user_messages and user.id in self.user_messages[guild.id]:
                self.user_messages[guild_id][user.id].clear()

            # Remove from timeout tracking after delay
            await asyncio.sleep(300)  # 5 minutes
            self.users_in_timeout.discard(user_timeout_key)

        except Exception as e:
            print(f"Error handling spam violation: {e}")
            self.users_in_timeout.discard(user_timeout_key)

    async def send_spam_log(self, guild, user, message, settings, timeout_applied):
        """Send spam log to designated log channel."""
        log_channel_id = settings.get('log_channel_id')
        if not log_channel_id:
            return

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        try:
            embed = discord.Embed(
                title=f"{emoji_warn} × Anti-Spam Verstoß",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name=f"{emoji_member} × Benutzer",
                value=f"{user.mention} ({user.id})",
                inline=True
            )
            embed.add_field(
                name=f"{emoji_channel} × Kanal",
                value=message.channel.mention,
                inline=True
            )
            embed.add_field(
                name=f"{emoji_moderator} × Aktion",
                value="Timeout (5 Min)" if timeout_applied else "Warnung",
                inline=True
            )
            embed.add_field(
                name=f"{emoji_statistics} × Limit",
                value=f"{settings['max_messages']} Nachrichten in {settings['time_frame']}s",
                inline=True
            )
            embed.add_field(
                name=f"{emoji_annoattention} × Nachricht (Vorschau)",
                value=f"```{message.content[:100]}{'...' if len(message.content) > 100 else ''}```",
                inline=False
            )
            embed.set_footer(text=f"User ID: {user.id}")
            embed.set_thumbnail(url=user.display_avatar.url)

            await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending spam log: {e}")

    async def delete_recent_messages(self, channel, user, limit=5):
        """Delete recent messages from a user."""
        try:
            messages_to_delete = []
            async for msg in channel.history(limit=50):  # Check last 50 messages
                if msg.author == user and len(messages_to_delete) < limit:
                    messages_to_delete.append(msg)
                if len(messages_to_delete) >= limit:
                    break

            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass  # Message already deleted
                except discord.Forbidden:
                    break  # No permission to delete

        except Exception as e:
            print(f"Error deleting messages: {e}")

    @antispam.command(name="setup", description="Richte das Anti-Spam-System ein.")
    async def setup_antispam(self, ctx, log_channel: discord.TextChannel, max_messages: int = 5, time_frame: int = 10):
        """Richte das Anti-Spam-System mit einem Log-Channel ein."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(f"{emoji_no} × Du benötigst die 'Server verwalten' Berechtigung für diesen Befehl.", ephemeral=True)
            return

        if max_messages < 1 or max_messages > 50:
            await ctx.respond(f"{emoji_no} × Maximale Nachrichten müssen zwischen 1 und 50 liegen.", ephemeral=True)
            return

        if time_frame < 1 or time_frame > 300:
            await ctx.respond(f"{emoji_no} × Zeitrahmen muss zwischen 1 und 300 Sekunden liegen.", ephemeral=True)
            return

        # Check if bot can send messages to log channel
        if not log_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.respond(f"{emoji_no} × Ich habe keine Berechtigung, Nachrichten in den angegebenen Log-Channel zu senden.",
                              ephemeral=True)
            return

        self.db.set_spam_settings(ctx.guild.id, max_messages, time_frame, log_channel.id)

        embed = discord.Embed(
            title=f"{emoji_yes} × Anti-Spam-System eingerichtet",
            color=discord.Color.green()
        )
        embed.add_field(
            name=f"{emoji_channel} × Log-Channel",
            value=log_channel.mention,
            inline=True
        )
        embed.add_field(
            name=f"{emoji_annoattention} × Nachrichtenlimit",
            value=f"{max_messages} Nachrichten",
            inline=True
        )
        embed.add_field(
            name=f"{emoji_statistics} × Zeitrahmen",
            value=f"{time_frame} Sekunden",
            inline=True
        )
        embed.add_field(
            name=f"{emoji_owner} × Status",
            value="🟢 Aktiv",
            inline=False
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="set", description="Ändere Anti-Spam-Parameter.")
    async def set_parameters(self, ctx, max_messages: int = None, time_frame: int = None):
        """Ändere die Anti-Spam-Parameter (Log-Channel bleibt unverändert)."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(f"{emoji_no} × Du benötigst die 'Server verwalten' Berechtigung für diesen Befehl.", ephemeral=True)
            return

        # Get current settings
        current_settings = self.db.get_spam_settings(ctx.guild.id)
        if not current_settings:
            await ctx.respond(f"{emoji_no} × Anti-Spam-System wurde noch nicht eingerichtet. Verwende `/antispam setup` zuerst.",
                              ephemeral=True)
            return

        # Use current values if not provided
        new_max_messages = max_messages if max_messages is not None else current_settings['max_messages']
        new_time_frame = time_frame if time_frame is not None else current_settings['time_frame']

        if new_max_messages < 5 or new_max_messages > 50:
            await ctx.respond(f"{emoji_no} × Maximale Nachrichten müssen zwischen 5 und 50 liegen.", ephemeral=True)
            return

        if new_time_frame < 5 or new_time_frame > 300:
            await ctx.respond(f"{emoji_no} × Zeitrahmen muss zwischen 5 und 300 Sekunden liegen.", ephemeral=True)
            return

        self.db.set_spam_settings(ctx.guild.id, new_max_messages, new_time_frame, current_settings['log_channel_id'])

        embed = discord.Embed(
            title=f"{emoji_owner} × Anti-Spam Einstellungen aktualisiert",
            description=f"Maximal **{new_max_messages}** Nachrichten in **{new_time_frame}** Sekunden erlaubt.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="log-channel", description="Ändere den Log-Channel.")
    async def set_log_channel(self, ctx, log_channel: discord.TextChannel):
        """Ändere den Log-Channel für Anti-Spam."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(f"{emoji_no} × Du benötigst die 'Server verwalten' Berechtigung für diesen Befehl.", ephemeral=True)
            return

        # Check if bot can send messages to log channel
        if not log_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.respond(f"{emoji_no} × Ich habe keine Berechtigung, Nachrichten in den angegebenen Log-Channel zu senden.",
                              ephemeral=True)
            return

        self.db.set_log_channel(ctx.guild.id, log_channel.id)

        embed = discord.Embed(
            title=f"{emoji_owner} × Log-Channel aktualisiert",
            description=f"Anti-Spam-Logs werden nun in {log_channel.mention} gesendet.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="view", description="Zeige aktuelle Anti-Spam-Einstellungen an.")
    async def view_settings(self, ctx):
        """Zeigt die aktuellen Anti-Spam-Einstellungen an."""
        settings = self.db.get_spam_settings(ctx.guild.id)

        if settings and settings.get('log_channel_id'):
            log_channel = ctx.guild.get_channel(settings['log_channel_id'])
            log_channel_display = log_channel.mention if log_channel else f"{emoji_warn} × Channel nicht gefunden"

            embed = discord.Embed(
                title=f"{emoji_owner} × Anti-Spam Einstellungen",
                color=discord.Color.blue()
            )
            embed.add_field(
                name=f"{emoji_channel} × Log-Channel",
                value=log_channel_display,
                inline=True
            )
            embed.add_field(
                name=f"{emoji_annoattention} × Nachrichtenlimit",
                value=f"{settings['max_messages']} Nachrichten",
                inline=True
            )
            embed.add_field(
                name=f"{emoji_statistics} × Zeitrahmen",
                value=f"{settings['time_frame']} Sekunden",
                inline=True
            )
            embed.add_field(
                name=f"{emoji_owner} × Status",
                value="🟢 Aktiv",
                inline=False
            )
        else:
            embed = discord.Embed(
                title=f"{emoji_owner} × Anti-Spam Einstellungen",
                description=f"{emoji_no} × **Anti-Spam-System nicht eingerichtet**\n\nVerwende `/antispam setup` um das System zu konfigurieren.",
                color=discord.Color.red()
            )

        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="logs", description="Zeige Anti-Spam-Logs an.")
    async def view_logs(self, ctx, limit: int = 10):
        """Zeigt die Anti-Spam-Protokolle an."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(f"{emoji_no} × Du benötigst die 'Server verwalten' Berechtigung für diesen Befehl.", ephemeral=True)
            return

        logs = self.db.get_spam_logs(ctx.guild.id, limit)

        if logs:
            embed = discord.Embed(
                title=f"{emoji_statistics} × Anti-Spam Protokolle",
                color=discord.Color.red()
            )

            log_text = ""
            for i, log in enumerate(logs, 1):
                user_id, message_preview, timestamp = log
                # Try to get user mention, fallback to ID
                try:
                    user = self.bot.get_user(user_id)
                    user_display = user.mention if user else f"<@{user_id}>"
                except:
                    user_display = f"User ID: {user_id}"

                log_text += f"**{i}.** {user_display}\n"
                log_text += f"📝 `{message_preview[:50]}{'...' if len(message_preview) > 50 else ''}`\n"
                log_text += f"🕒 {timestamp}\n\n"

            embed.description = log_text
            embed.set_footer(text=f"Zeige die letzten {len(logs)} Einträge")
        else:
            embed = discord.Embed(
                title=f"{emoji_statistics} × Anti-Spam Protokolle",
                description="Für diesen Server wurden keine Anti-Spam-Logs gefunden.",
                color=discord.Color.green()
            )

        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="clear", description="Lösche alle Anti-Spam-Logs für diesen Server.")
    async def clear_logs(self, ctx):
        """Löscht alle Anti-Spam-Protokolle für den Server."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(f"{emoji_no} × Du benötigst Administrator-Rechte für diesen Befehl.", ephemeral=True)
            return

        self.db.clear_spam_logs(ctx.guild.id)

        embed = discord.Embed(
            title=f"{emoji_yes} × Protokolle gelöscht",
            description="Alle Anti-Spam-Protokolle für diesen Server wurden gelöscht.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="whitelist", description="Füge einen Benutzer zur Whitelist hinzu.")
    async def add_whitelist(self, ctx, user: discord.Member):
        """Fügt einen Benutzer zur Anti-Spam Whitelist hinzu."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(f"{emoji_no} × Du benötigst die 'Server verwalten' Berechtigung für diesen Befehl.", ephemeral=True)
            return

        self.db.add_to_whitelist(ctx.guild.id, user.id)

        embed = discord.Embed(
            title=f"{emoji_yes} × Zur Whitelist hinzugefügt",
            description=f"{user.mention} wurde zur Anti-Spam Whitelist hinzugefügt.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @antispam.command(name="disable", description="Deaktiviere das Anti-Spam-System.")
    async def disable_antispam(self, ctx):
        """Deaktiviert das Anti-Spam-System für diesen Server."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(f"{emoji_no} × Du benötigst Administrator-Rechte für diesen Befehl.", ephemeral=True)
            return

        # Remove settings to disable the system
        with self.db.conn:
            self.db.conn.execute('DELETE FROM spam_settings WHERE guild_id = ?', (ctx.guild.id,))

        embed = discord.Embed(
            title=f"{emoji_delete} × Anti-Spam-System deaktiviert",
            description="Das Anti-Spam-System wurde für diesen Server deaktiviert.\nVerwende `/antispam setup` um es wieder zu aktivieren.",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    def is_whitelisted(self, guild_id, user_id):
        """Check if user is whitelisted."""
        return self.db.is_whitelisted(guild_id, user_id)


def setup(bot: ezcord.Bot):
    bot.add_cog(AntiSpam(bot))