# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord.ext import commands, tasks
from discord import slash_command, Option, SlashCommandGroup
from DevTools import db
import asyncio
import logging
import re
import time
from typing import List, Optional, Dict
import json
from datetime import datetime, timedelta
import ezcord

from discord.ui import Container
# Logger konfigurieren
logger = logging.getLogger(__name__)


class globalchat(ezcord.Cog, group="globalchat"):
    def __init__(self, bot):
        self.bot = bot



        # Rate limiting für Spam-Schutz
        self.message_cooldown = commands.CooldownMapping.from_cooldown(
            5, 60, commands.BucketType.user  # 5 Nachrichten pro Minute pro User
        )

        # Cache für Channel-IDs (alle 3 Minuten aktualisiert)
        self._channel_cache: List[int] = []
        self._cache_last_update = 0
        self.cache_duration = 180  # 3 Minuten

        # Content Filter Patterns
        self.bad_words = [
            r'(?i)\b(discord\.gg|discord\.com/invite|discordapp\.com/invite)\b',  # Discord Invites
            r'(?i)\b(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)\b',
            # URLs (optional)
        ]

        # Starte Background Tasks
        self.cleanup_task.start()
        self.cache_refresh_task.start()

    def cog_unload(self):
        """Cleanup beim Entladen des Cogs"""
        self.cleanup_task.cancel()
        self.cache_refresh_task.cancel()

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Tägliche Bereinigung alter Daten"""
        try:
            db.cleanup_old_data(30)
            logger.info("Tägliche Bereinigung abgeschlossen")
        except Exception as e:
            logger.error(f"Fehler bei der täglichen Bereinigung: {e}")

    @tasks.loop(minutes=3)
    async def cache_refresh_task(self):
        """Aktualisiert den Channel-Cache regelmäßig"""
        try:
            self._channel_cache = db.get_all_channels()
            self._cache_last_update = time.time()
            logger.debug(f"Channel-Cache aktualisiert: {len(self._channel_cache)} Channels")
        except Exception as e:
            logger.error(f"Fehler beim Cache-Update: {e}")

    @cleanup_task.before_loop
    @cache_refresh_task.before_loop
    async def before_tasks(self):
        """Warten bis Bot bereit ist"""
        await self.bot.wait_until_ready()

    async def _get_cached_channels(self) -> List[int]:
        """Holt Channel-IDs aus Cache oder DB"""
        current_time = time.time()

        if current_time - self._cache_last_update > self.cache_duration:
            self._channel_cache = db.get_all_channels()
            self._cache_last_update = current_time
            logger.debug(f"Channel cache manuell aktualisiert: {len(self._channel_cache)} Channels")

        return self._channel_cache

    def _is_valid_message(self, message: discord.Message) -> tuple[bool, str]:
        """Prüft ob die Nachricht valid für GlobalChat ist"""
        if message.author.bot:
            return False, "Bot-Nachricht"

        # Blacklist prüfen
        if db.is_blacklisted('user', message.author.id):
            return False, "User auf Blacklist"

        if db.is_blacklisted('guild', message.guild.id):
            return False, "Guild auf Blacklist"

        # Leere Nachrichten ignorieren
        if not message.content and not message.attachments:
            return False, "Leere Nachricht"

        # Sehr kurze Nachrichten ignorieren (Spam-Schutz)
        if message.content and len(message.content.strip()) < 2:
            return False, "Zu kurze Nachricht"

        # Guild-Settings prüfen
        settings = db.get_guild_settings(message.guild.id)

        # Message Length prüfen
        if message.content and len(message.content) > settings.get('max_message_length', 1900):
            return False, "Nachricht zu lang"

        # Content Filter
        if settings.get('filter_enabled', True):
            if self._contains_filtered_content(message.content):
                return False, "Gefilterte Inhalte"

        # NSFW Filter
        if settings.get('nsfw_filter', True):
            if self._is_nsfw_content(message.content):
                return False, "NSFW Inhalt"

        return True, "OK"

    def _contains_filtered_content(self, content: str) -> bool:
        """Prüft auf gefilterte Inhalte"""
        if not content:
            return False

        for pattern in self.bad_words:
            if re.search(pattern, content):
                return True
        return False

    def _is_nsfw_content(self, content: str) -> bool:
        """Einfache NSFW-Erkennung (kann erweitert werden)"""
        if not content:
            return False

        # Einfache Keywords - kann erweitert werden
        nsfw_keywords = ['nsfw', 'porn', 'sex', 'xxx']
        content_lower = content.lower()

        return any(keyword in content_lower for keyword in nsfw_keywords)

    def _clean_message_content(self, content: str) -> str:
        """Bereinigt Nachrichteninhalt von Discord-spezifischen Elementen"""
        if not content:
            return ""

        # Entferne @everyone und @here
        content = content.replace('@everyone', '＠everyone').replace('@here', '＠here')

        return content

    async def _create_message_embed(self, message: discord.Message) -> discord.Embed:
        """Erstellt ein Embed für die GlobalChat-Nachricht"""
        content = self._clean_message_content(message.content)
        author_name = message.author.display_name

        # Guild-Settings für Embed-Farbe
        settings = db.get_guild_settings(message.guild.id)
        embed_color_hex = settings.get('embed_color', '#5865F2')

        # Hex-String zu discord.Color konvertieren
        try:
            # Entferne das # am Anfang falls vorhanden
            color_hex = embed_color_hex.lstrip('#')
            # Konvertiere zu int mit base 16
            embed_color = discord.Color(int(color_hex, 16))
        except (ValueError, TypeError):
            # Fallback zu Discord's Standard-Blau
            embed_color = discord.Color.blurple()

        embed = discord.Embed(
            description=f"{content or '*Anhang oder Medien*'}",
            color=embed_color,
            timestamp=message.created_at
        )

        # --- Rollen und Badges ermitteln ---
        roles = []
        badges = []

        # Bot Owner Check
        bot_owner_ids = [1093555256689959005]  # Deine Bot-Owner-ID hier
        if message.author.id in bot_owner_ids:
            badges.append("👑")
            roles.append("Bot Owner")
        elif hasattr(self.bot, "owner_ids") and message.author.id in self.bot.owner_ids:
            badges.append("🛠️")
            roles.append("Developer")

        # Server-spezifische Rollen
        if message.author.guild_permissions.administrator:
            badges.append("⚡")
            roles.append("Admin")
        elif message.author.guild_permissions.manage_guild:
            badges.append("🔧")
            roles.append("Mod")

        # Booster Check
        if hasattr(message.author, 'premium_since') and message.author.premium_since:
            badges.append("💎")
            roles.append("Booster")

        # Author-Feld zusammenbauen
        author_text = f"{''.join(badges)} {author_name}"
        if roles:
            author_text += f" • {' | '.join(roles)}"

        embed.set_author(
            name=author_text,
            icon_url=message.author.display_avatar.url
        )

        # Server-Info im Footer
        embed.set_footer(
            text=f"📍 {message.guild.name} • #{message.channel.name}",
            icon_url=message.guild.icon.url if message.guild.icon else None
        )

        # Anhänge verarbeiten
        if message.attachments:
            image_set = False
            attachment_lines = []

            for attachment in message.attachments:
                # Erstes Bild als Embed-Image
                if attachment.content_type and attachment.content_type.startswith("image/") and not image_set:
                    embed.set_image(url=attachment.url)
                    image_set = True
                else:
                    # Andere Anhänge als Links
                    attachment_lines.append(f"📎 [{attachment.filename}]({attachment.url})")

            if attachment_lines:
                embed.add_field(name="📎 Weitere Anhänge", value="\n".join(attachment_lines), inline=False)

        return embed

    async def _send_to_channel(self, channel_id: int, embed: discord.Embed) -> bool:
        """Sendet Embed an einen spezifischen Channel"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False

            await channel.send(embed=embed)
            return True

        except discord.Forbidden:
            logger.warning(f"Keine Berechtigung für Channel {channel_id}")
            return False
        except discord.HTTPException as e:
            logger.error(f"HTTP-Fehler beim Senden an Channel {channel_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unbekannter Fehler beim Senden an Channel {channel_id}: {e}")
            return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Hauptlogik für GlobalChat-Nachrichten"""
        # Basis-Validierung
        is_valid, reason = self._is_valid_message(message)
        if not is_valid:
            logger.debug(f"Nachricht abgelehnt: {reason}")
            return

        # Rate limiting prüfen
        bucket = self.message_cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            try:
                await message.add_reaction("⏰")
                await asyncio.sleep(3)
                await message.remove_reaction("⏰", self.bot.user)
            except (discord.Forbidden, discord.NotFound):
                pass
            return

        # Channel-IDs aus Cache holen
        channel_ids = await self._get_cached_channels()

        # Prüfen, ob Nachricht in einem GlobalChat-Channel geschrieben wurde
        if message.channel.id not in channel_ids:
            return

        # Message loggen
        attachment_urls = [att.url for att in message.attachments] if message.attachments else None
        db.log_message(
            message.author.id,
            message.guild.id,
            message.channel.id,
            message.content,
            attachment_urls
        )

        # Aktivität aktualisieren
        db.update_channel_activity(message.guild.id)
        db.update_daily_stats()

        try:
            # Originalnachricht löschen
            await message.delete()
        except discord.Forbidden:
            logger.warning(f"Keine Berechtigung zum Löschen in Channel {message.channel.id}")
            return  # Wenn wir nicht löschen können, nicht weiterleiten
        except discord.NotFound:
            pass

        # Embed erstellen
        try:
            embed = await self._create_message_embed(message)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Embeds: {e}")
            return

        # Nachricht an alle anderen GlobalChat-Channels senden
        successful_sends = 0
        failed_sends = 0

        # Parallele Verarbeitung für bessere Performance
        tasks = []
        for channel_id in channel_ids:
            task = self._send_to_channel(channel_id, embed)
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_sends = sum(1 for result in results if result is True)
            failed_sends = len(results) - successful_sends

        logger.info(f"GlobalChat-Nachricht versendet: {successful_sends} erfolgreich, {failed_sends} fehlgeschlagen")

    # --- Slash Commands ---

    globalchat = SlashCommandGroup("globalchat", "Commands für den GlobalChat")

    @globalchat.command(
        name="setup",
        description="Richtet einen GlobalChat-Channel ein"
    )
    async def setup_globalchat(
            self,
            ctx: discord.ApplicationContext,
            channel: Option(discord.TextChannel, "Der Channel für den GlobalChat", required=True)
    ):
        """Setup-Command für GlobalChat"""
        # Permissions prüfen
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("❌ Du benötigst die `Server verwalten` Berechtigung!", ephemeral=True)
            return

        # Bot Permissions prüfen
        bot_perms = channel.permissions_for(ctx.guild.me)
        if not (bot_perms.send_messages and bot_perms.manage_messages and bot_perms.embed_links):
            await ctx.respond(
                "❌ Der Bot benötigt folgende Berechtigungen im Channel:\n"
                "• Nachrichten senden\n"
                "• Nachrichten verwalten\n"
                "• Links einbetten",
                ephemeral=True
            )
            return

        # Channel in DB setzen
        success = db.set_globalchat_channel(
            ctx.guild.id,
            channel.id,
            ctx.guild.name,
            channel.name
        )

        if success:
            # Cache invalidieren
            self._channel_cache = []
            self._cache_last_update = 0

            container = Container()
            container.add_text(
                "## 🌍 GlobalChat eingerichtet!"
            )
            container.add_separator()
            container.add_text(
                f"Der Channel {channel.mention} wurde als GlobalChat-Channel eingerichtet.\n\n"
                "**Wie es funktioniert:**\n"
                "• Nachrichten in diesem Channel werden an alle anderen GlobalChat-Server gesendet\n"
                "• Die ursprüngliche Nachricht wird gelöscht und als Embed neu gesendet\n"
                "• Rate-Limiting: 5 Nachrichten pro Minute pro User\n"
                "-# Nutze /globalchat_settings für weitere Einstellungen"
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)
        else:
            await ctx.respond("❌ Fehler beim Einrichten des GlobalChat-Channels!", ephemeral=True)

    @globalchat.command(
        name="remove",
        description="Entfernt den GlobalChat-Channel von diesem Server"
    )
    async def remove_globalchat(self, ctx: discord.ApplicationContext):
        """Entfernt GlobalChat vom Server"""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("❌ Du benötigst die `Server verwalten` Berechtigung!", ephemeral=True)
            return

        success = db.remove_globalchat_channel(ctx.guild.id)

        if success:
            # Cache invalidieren
            self._channel_cache = []
            self._cache_last_update = 0

            container = Container()
            container.add_text(
                "# 🗑️ GlobalChat entfernt\n"
            )
            container.add_separator()
            container.add_text(
                "Der GlobalChat-Channel wurde von diesem Server entfernt."
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)
        else:
            await ctx.respond("❌ Kein GlobalChat-Channel auf diesem Server gefunden!", ephemeral=True)

    @globalchat.command(
        name="stats",
        description="Zeigt GlobalChat-Statistiken"
    )
    async def globalchat_stats(self, ctx: discord.ApplicationContext):
        """Zeigt Statistiken"""
        stats = db.get_global_stats()

        if not stats:
            await ctx.respond("❌ Fehler beim Abrufen der Statistiken!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🌍 GlobalChat Statistiken",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📊 Server & Nachrichten",
            value=f"**Aktive Server:** {stats.get('active_guilds', 0):,}\n"
                  f"**Nachrichten insgesamt:** {stats.get('total_messages', 0):,}\n"
                  f"**Nachrichten heute:** {stats.get('today_messages', 0):,}",
            inline=False
        )

        embed.add_field(
            name="🚫 Moderation",
            value=f"**Gesperrte User:** {stats.get('banned_users', 0):,}\n"
                  f"**Gesperrte Server:** {stats.get('banned_guilds', 0):,}",
            inline=False
        )

        embed.set_footer(text=f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

        await ctx.respond(embed=embed)

    @globalchat.command(
        name="settings",
        description="Konfiguriert GlobalChat-Einstellungen für diesen Server"
    )
    async def globalchat_settings(
            self,
            ctx: discord.ApplicationContext,
            filter_enabled: Option(bool, "Content-Filter aktiviert", required=False),
            nsfw_filter: Option(bool, "NSFW-Filter aktiviert", required=False),
            embed_color: Option(str, "Farbe der Embeds (Hex-Code, z.B. #FF0000)", required=False),
            max_message_length: Option(int, "Maximale Nachrichtenlänge (50-2000)", required=False, min_value=50,
                                       max_value=2000)
    ):
        """Einstellungen verwalten"""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("❌ Du benötigst die `Server verwalten` Berechtigung!", ephemeral=True)
            return

        # Prüfen ob Server GlobalChat nutzt
        if not db.get_globalchat_channel(ctx.guild.id):
            await ctx.respond("❌ Dieser Server nutzt GlobalChat nicht! Nutze `/globalchat_setup` zuerst.",
                              ephemeral=True)
            return

        updated_settings = []

        # Einstellungen einzeln aktualisieren
        if filter_enabled is not None:
            if db.update_guild_setting(ctx.guild.id, 'filter_enabled', filter_enabled):
                updated_settings.append(f"Content-Filter: {'An' if filter_enabled else 'Aus'}")

        if nsfw_filter is not None:
            if db.update_guild_setting(ctx.guild.id, 'nsfw_filter', nsfw_filter):
                updated_settings.append(f"NSFW-Filter: {'An' if nsfw_filter else 'Aus'}")

        if embed_color:
            # Hex-Farbe validieren
            if re.match(r'^#[0-9a-fA-F]{6}$', embed_color):
                if db.update_guild_setting(ctx.guild.id, 'embed_color', embed_color):
                    updated_settings.append(f"Embed-Farbe: {embed_color}")
            else:
                await ctx.respond("❌ Ungültiger Hex-Farbcode! Format: #RRGGBB", ephemeral=True)
                return

        if max_message_length:
            if db.update_guild_setting(ctx.guild.id, 'max_message_length', max_message_length):
                updated_settings.append(f"Max. Nachrichtenlänge: {max_message_length}")

        if updated_settings:
            embed = discord.Embed(
                title="⚙️ Einstellungen aktualisiert",
                description="\n".join(f"• {setting}" for setting in updated_settings),
                color=discord.Color.green()
            )
        else:
            # Aktuelle Einstellungen anzeigen
            current_settings = db.get_guild_settings(ctx.guild.id)
            embed = discord.Embed(
                title="⚙️ Aktuelle GlobalChat-Einstellungen",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Filter & Limits",
                value=f"**Content-Filter:** {'An' if current_settings.get('filter_enabled') else 'Aus'}\n"
                      f"**NSFW-Filter:** {'An' if current_settings.get('nsfw_filter') else 'Aus'}\n"
                      f"**Max. Nachrichtenlänge:** {current_settings.get('max_message_length', 1900)}",
                inline=False
            )
            embed.add_field(
                name="Design",
                value=f"**Embed-Farbe:** {current_settings.get('embed_color', '#5865F2')}",
                inline=False
            )

        await ctx.respond(embed=embed)

    # --- Admin Commands (nur für Bot-Owner) ---

    @globalchat.command(
        name="ban",
        description="[ADMIN] Sperrt einen User oder Server vom GlobalChat"
    )
    async def ban_from_globalchat(
            self,
            ctx: discord.ApplicationContext,
            entity_type: Option(str, "Was sperren", choices=["user", "guild"]),
            entity_id: Option(str, "User-ID oder Server-ID"),
            reason: Option(str, "Grund für die Sperre"),
            duration: Option(int, "Dauer in Stunden (leer = permanent)", required=False)
    ):
        """Bannt User oder Guilds vom GlobalChat"""
        # Nur Bot-Owner
        if ctx.author.id not in [1093555256689959005]:  # Deine ID hier
            await ctx.respond("❌ Nur Bot-Owner können diesen Command nutzen!", ephemeral=True)
            return

        try:
            entity_id = int(entity_id)
        except ValueError:
            await ctx.respond("❌ Ungültige ID!", ephemeral=True)
            return

        success = db.add_to_blacklist(entity_type, entity_id, reason, ctx.author.id, duration)

        if success:
            duration_text = f"{duration} Stunden" if duration else "Permanent"
            embed = discord.Embed(
                title="🔨 GlobalChat-Sperre verhängt",
                color=discord.Color.red()
            )
            embed.add_field(name="Typ", value=entity_type.title(), inline=True)
            embed.add_field(name="ID", value=str(entity_id), inline=True)
            embed.add_field(name="Dauer", value=duration_text, inline=True)
            embed.add_field(name="Grund", value=reason, inline=False)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("❌ Fehler beim Verhängen der Sperre!", ephemeral=True)

    @globalchat.command(
        name="unban",
        description="[ADMIN] Entsperrt einen User oder Server"
    )
    async def unban_from_globalchat(
            self,
            ctx: discord.ApplicationContext,
            entity_type: Option(str, "Was entsperren", choices=["user", "guild"]),
            entity_id: Option(str, "User-ID oder Server-ID")
    ):
        """Entbannt User oder Guilds"""
        if ctx.author.id not in [1093555256689959005]:  # Deine ID hier
            await ctx.respond("❌ Nur Bot-Owner können diesen Command nutzen!", ephemeral=True)
            return

        try:
            entity_id = int(entity_id)
        except ValueError:
            await ctx.respond("❌ Ungültige ID!", ephemeral=True)
            return

        success = db.remove_from_blacklist(entity_type, entity_id)

        if success:
            embed = discord.Embed(
                title="✅ GlobalChat-Sperre aufgehoben",
                description=f"{entity_type.title()} `{entity_id}` wurde entsperrt.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("❌ Keine Sperre für diese ID gefunden!", ephemeral=True)


def setup(bot):
    bot.add_cog(globalchat(bot))