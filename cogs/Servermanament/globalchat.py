# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord.ext import commands, tasks
from discord import slash_command, Option, SlashCommandGroup
from DevTools.backend.database.globalchat_db import GlobalChatDatabase
db = GlobalChatDatabase()
import asyncio
import logging
import re
import time
from typing import List, Optional, Dict, Tuple
import json
from datetime import datetime, timedelta
import ezcord
from collections import defaultdict

from discord.ui import Container

# Logger konfigurieren
logger = logging.getLogger(__name__)


class GlobalChatConfig:
    """Zentrale Konfiguration für GlobalChat"""
    RATE_LIMIT_MESSAGES = 5
    RATE_LIMIT_SECONDS = 60
    CACHE_DURATION = 180  # 3 Minuten
    CLEANUP_DAYS = 30
    MIN_MESSAGE_LENGTH = 2
    DEFAULT_MAX_MESSAGE_LENGTH = 1900
    DEFAULT_EMBED_COLOR = '#5865F2'
    
    # Bot Owner IDs
    BOT_OWNERS = [1093555256689959005]
    
    # Content Filter Patterns
    DISCORD_INVITE_PATTERN = r'(?i)\b(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[a-zA-Z0-9]+\b'
    URL_PATTERN = r'(?i)\bhttps?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F]{2}))+\b'
    
    # NSFW Keywords (erweitert)
    NSFW_KEYWORDS = [
        'nsfw', 'porn', 'sex', 'xxx', 'nude', 'hentai', 
        'dick', 'pussy', 'cock', 'tits', 'ass', 'fuck'
    ]


class MessageValidator:
    """Validiert und filtert Nachrichten"""
    
    def __init__(self, config: GlobalChatConfig):
        self.config = config
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Kompiliert Regex-Patterns für bessere Performance"""
        self.invite_pattern = re.compile(self.config.DISCORD_INVITE_PATTERN)
        self.url_pattern = re.compile(self.config.URL_PATTERN)
    
    def validate_message(self, message: discord.Message, settings: Dict) -> Tuple[bool, str]:
        """Hauptvalidierung für Nachrichten"""
        # Bot-Nachrichten ignorieren
        if message.author.bot:
            return False, "Bot-Nachricht"
        
        # Blacklist prüfen
        if db.is_blacklisted('user', message.author.id):
            return False, "User auf Blacklist"
        
        if db.is_blacklisted('guild', message.guild.id):
            return False, "Guild auf Blacklist"
        
        # Leere Nachrichten
        if not message.content and not message.attachments:
            return False, "Leere Nachricht"
        
        # Nachrichtenlänge
        if message.content:
            content_length = len(message.content.strip())
            
            if content_length < self.config.MIN_MESSAGE_LENGTH:
                return False, "Zu kurze Nachricht"
            
            max_length = settings.get('max_message_length', self.config.DEFAULT_MAX_MESSAGE_LENGTH)
            if content_length > max_length:
                return False, f"Nachricht zu lang (max. {max_length} Zeichen)"
        
        # Content Filter
        if settings.get('filter_enabled', True):
            is_filtered, filter_reason = self.check_filtered_content(message.content)
            if is_filtered:
                return False, f"Gefilterte Inhalte: {filter_reason}"
        
        # NSFW Filter
        if settings.get('nsfw_filter', True):
            if self.check_nsfw_content(message.content):
                return False, "NSFW Inhalt erkannt"
        
        return True, "OK"
    
    def check_filtered_content(self, content: str) -> Tuple[bool, str]:
        """Prüft auf gefilterte Inhalte mit detailliertem Grund"""
        if not content:
            return False, ""
        
        # Discord Invites
        if self.invite_pattern.search(content):
            return True, "Discord Invite"
        
        # Optional: URLs filtern (auskommentiert, da manchmal gewünscht)
        # if self.url_pattern.search(content):
        #     return True, "URL"
        
        return False, ""
    
    def check_nsfw_content(self, content: str) -> bool:
        """Erweiterte NSFW-Erkennung"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # Keyword-Check mit Wortgrenzen
        for keyword in self.config.NSFW_KEYWORDS:
            # Mit Wortgrenzen für bessere Genauigkeit
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    def clean_content(self, content: str) -> str:
        """Bereinigt Nachrichteninhalt"""
        if not content:
            return ""
        
        # @everyone und @here neutralisieren
        content = content.replace('@everyone', '＠everyone')
        content = content.replace('@here', '＠here')
        
        # Rolle-Mentions neutralisieren
        content = re.sub(r'<@&(\d+)>', r'＠role', content)
        
        return content


class EmbedBuilder:
    """Erstellt formatierte Embeds für GlobalChat"""
    
    def __init__(self, config: GlobalChatConfig):
        self.config = config
    
    async def create_message_embed(self, message: discord.Message, settings: Dict) -> discord.Embed:
        """Erstellt ein verbessertes Embed für GlobalChat-Nachrichten"""
        content = self._clean_content(message.content)
        
        # Embed-Farbe
        embed_color = self._parse_color(settings.get('embed_color', self.config.DEFAULT_EMBED_COLOR))
        
        # Beschreibung mit Fallback
        description = content if content else "*Medien oder Anhang*"
        
        embed = discord.Embed(
            description=description,
            color=embed_color,
            timestamp=message.created_at
        )
        
        # Author mit Badges
        author_text, badges = self._build_author_info(message.author)
        embed.set_author(
            name=author_text,
            icon_url=message.author.display_avatar.url
        )
        
        # Footer mit Server-Info
        footer_text = f"📍 {message.guild.name} • #{message.channel.name}"
        embed.set_footer(
            text=footer_text,
            icon_url=message.guild.icon.url if message.guild.icon else None
        )
        
        # Anhänge verarbeiten
        if message.attachments:
            self._process_attachments(embed, message.attachments)
        
        # Sticker Support
        if message.stickers:
            sticker_text = " • ".join([f":{sticker.name}:" for sticker in message.stickers])
            embed.add_field(name="🎨 Sticker", value=sticker_text, inline=False)
        
        return embed
    
    def _clean_content(self, content: str) -> str:
        """Bereinigt Nachrichteninhalt"""
        if not content:
            return ""
        
        content = content.replace('@everyone', '＠everyone')
        content = content.replace('@here', '＠here')
        content = re.sub(r'<@&(\d+)>', r'＠role', content)
        
        return content.strip()
    
    def _parse_color(self, color_hex: str) -> discord.Color:
        """Parst Hex-Farbe zu discord.Color"""
        try:
            color_hex = color_hex.lstrip('#')
            return discord.Color(int(color_hex, 16))
        except (ValueError, TypeError):
            return discord.Color.blurple()
    
    def _build_author_info(self, author: discord.Member) -> Tuple[str, List[str]]:
        """Baut Author-Text mit Badges"""
        badges = []
        roles = []
        
        # Bot Owner
        if author.id in self.config.BOT_OWNERS:
            badges.append("👑")
            roles.append("Bot Owner")
        
        # Server Admin/Mod
        if author.guild_permissions.administrator:
            badges.append("⚡")
            roles.append("Admin")
        elif author.guild_permissions.manage_guild:
            badges.append("🔧")
            roles.append("Mod")
        
        # Booster
        if hasattr(author, 'premium_since') and author.premium_since:
            badges.append("💎")
            roles.append("Booster")
        
        # Account-Alter Badge (optional)
        account_age = (datetime.now(author.created_at.tzinfo) - author.created_at).days
        if account_age < 30:
            badges.append("🆕")
        
        # Author-Text zusammenbauen
        badge_str = ''.join(badges) + ' ' if badges else ''
        author_text = f"{badge_str}{author.display_name}"
        
        if roles:
            author_text += f" • {' | '.join(roles)}"
        
        return author_text, badges
    
    def _process_attachments(self, embed: discord.Embed, attachments: List[discord.Attachment]):
        """Verarbeitet Anhänge für Embed"""
        image_set = False
        attachment_lines = []
        
        for attachment in attachments:
            # Erstes Bild als Embed-Image
            if attachment.content_type and attachment.content_type.startswith("image/"):
                if not image_set:
                    embed.set_image(url=attachment.url)
                    image_set = True
                else:
                    attachment_lines.append(f"🖼️ [{attachment.filename}]({attachment.url})")
            elif attachment.content_type and attachment.content_type.startswith("video/"):
                attachment_lines.append(f"🎥 [{attachment.filename}]({attachment.url})")
            else:
                attachment_lines.append(f"📎 [{attachment.filename}]({attachment.url})")
        
        if attachment_lines:
            embed.add_field(
                name="📎 Weitere Anhänge",
                value="\n".join(attachment_lines[:5]),  # Max 5 anzeigen
                inline=False
            )


class GlobalChat(ezcord.Cog, group="globalchat"):
    """Hauptklasse für GlobalChat-Funktionalität"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = GlobalChatConfig()
        self.validator = MessageValidator(self.config)
        self.embed_builder = EmbedBuilder(self.config)
        
        # Rate Limiting
        self.message_cooldown = commands.CooldownMapping.from_cooldown(
            self.config.RATE_LIMIT_MESSAGES,
            self.config.RATE_LIMIT_SECONDS,
            commands.BucketType.user
        )
        
        # Channel Cache
        self._channel_cache: List[int] = []
        self._cache_last_update = 0
        
        # Message Queue für besseres Batch-Processing
        self._message_queue: Dict[int, List[discord.Embed]] = defaultdict(list)
        
        # Background Tasks starten
        self.cleanup_task.start()
        self.cache_refresh_task.start()
    
    def cog_unload(self):
        """Cleanup beim Entladen"""
        self.cleanup_task.cancel()
        self.cache_refresh_task.cancel()
    
    # ==================== Background Tasks ====================
    
    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Tägliche Bereinigung alter Daten"""
        try:
            db.cleanup_old_data(self.config.CLEANUP_DAYS)
            logger.info("✅ Tägliche Bereinigung abgeschlossen")
        except Exception as e:
            logger.error(f"❌ Fehler bei Bereinigung: {e}", exc_info=True)
    
    @tasks.loop(minutes=3)
    async def cache_refresh_task(self):
        """Aktualisiert Channel-Cache regelmäßig"""
        try:
            self._channel_cache = db.get_all_channels()
            self._cache_last_update = time.time()
            logger.debug(f"🔄 Cache aktualisiert: {len(self._channel_cache)} Channels")
        except Exception as e:
            logger.error(f"❌ Cache-Update Fehler: {e}", exc_info=True)
    
    @cleanup_task.before_loop
    @cache_refresh_task.before_loop
    async def before_tasks(self):
        """Warten bis Bot bereit ist"""
        await self.bot.wait_until_ready()
    
    # ==================== Cache Management ====================
    
    async def _get_cached_channels(self) -> List[int]:
        """Holt Channel-IDs aus Cache oder DB"""
        current_time = time.time()
        
        if current_time - self._cache_last_update > self.config.CACHE_DURATION:
            self._channel_cache = db.get_all_channels()
            self._cache_last_update = current_time
            logger.debug(f"🔄 Cache manuell aktualisiert: {len(self._channel_cache)} Channels")
        
        return self._channel_cache
    
    def _invalidate_cache(self):
        """Invalidiert den Channel-Cache"""
        self._channel_cache = []
        self._cache_last_update = 0
    
    # ==================== Message Handling ====================
    
    async def _send_to_channel(self, channel_id: int, embed: discord.Embed) -> bool:
        """Sendet Embed an spezifischen Channel mit Error-Handling"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"⚠️ Channel {channel_id} nicht gefunden")
                return False
            
            # Permissions prüfen
            if not channel.permissions_for(channel.guild.me).send_messages:
                logger.warning(f"⚠️ Keine Send-Permission in {channel_id}")
                return False
            
            await channel.send(embed=embed)
            return True
            
        except discord.Forbidden:
            logger.warning(f"⚠️ Forbidden in Channel {channel_id}")
            return False
        except discord.HTTPException as e:
            if e.status == 429:  # Rate Limited
                logger.warning(f"⚠️ Rate Limited in Channel {channel_id}")
            else:
                logger.error(f"❌ HTTP Error {e.status} in Channel {channel_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unbekannter Fehler in Channel {channel_id}: {e}", exc_info=True)
            return False
    
    async def _send_to_all_channels(self, embed: discord.Embed, source_channel_id: int, exclude_source: bool = False) -> Tuple[int, int]:
        """Sendet Embed an alle GlobalChat-Channels (parallel)
        
        Args:
            embed: Das zu sendende Embed
            source_channel_id: Der Original-Channel
            exclude_source: Wenn True, wird der Source-Channel ausgeschlossen (nicht empfohlen)
        """
        channel_ids = await self._get_cached_channels()
        
        # Optional: Source-Channel ausschließen
        if exclude_source:
            channel_ids = [cid for cid in channel_ids if cid != source_channel_id]
        
        # Erstelle Tasks für paralleles Senden
        tasks = [
            self._send_to_channel(channel_id, embed)
            for channel_id in channel_ids
        ]
        
        if not tasks:
            return 0, 0
        
        # Führe alle Sends parallel aus
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        return successful, failed
    
    # ==================== Event Listeners ====================
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Hauptlogik für GlobalChat-Nachrichten"""
        # Basis-Checks
        if not message.guild or not hasattr(message.author, 'guild_permissions'):
            return
        
        # Channel-IDs laden
        channel_ids = await self._get_cached_channels()
        
        # Prüfen ob GlobalChat-Channel
        if message.channel.id not in channel_ids:
            return
        
        # Guild-Settings laden
        settings = db.get_guild_settings(message.guild.id)
        
        # Message validieren
        is_valid, reason = self.validator.validate_message(message, settings)
        if not is_valid:
            logger.debug(f"❌ Nachricht abgelehnt: {reason} (User: {message.author.id})")
            
            # Optional: User benachrichtigen bei bestimmten Gründen
            if "Blacklist" in reason or "NSFW" in reason or "Gefilterte" in reason:
                try:
                    await message.add_reaction("❌")
                    await asyncio.sleep(2)
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass
            return
        
        # Rate Limiting prüfen
        bucket = self.message_cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            try:
                await message.add_reaction("⏰")
                await asyncio.sleep(3)
                await message.remove_reaction("⏰", self.bot.user)
            except (discord.Forbidden, discord.NotFound):
                pass
            logger.debug(f"⏰ Rate Limited: User {message.author.id} ({retry_after:.1f}s)")
            return
        
        # Message loggen
        try:
            attachment_urls = [att.url for att in message.attachments] if message.attachments else None
            # Als komma-separierter String wie in der DB erwartet
            attachment_str = ",".join(attachment_urls) if attachment_urls else None
            
            db.log_message(
                message.author.id,
                message.guild.id,
                message.channel.id,
                message.content,
                attachment_str  # Als String, nicht als Liste
            )
        except Exception as e:
            logger.error(f"❌ Fehler beim Loggen: {e}")
        
        # Aktivität aktualisieren
        try:
            db.update_channel_activity(message.guild.id)
            db.update_daily_stats()
        except Exception as e:
            logger.error(f"❌ Fehler bei Aktivitäts-Update: {e}")
        
        # Original-Nachricht löschen
        try:
            await message.delete()
        except discord.Forbidden:
            logger.warning(f"⚠️ Keine Delete-Permission in {message.channel.id}")
            return  # Ohne Delete-Permission nicht weiterleiten
        except discord.NotFound:
            pass  # Bereits gelöscht
        
        # Embed erstellen
        try:
            embed = await self.embed_builder.create_message_embed(message, settings)
        except Exception as e:
            logger.error(f"❌ Fehler beim Embed-Erstellen: {e}", exc_info=True)
            return
        
        # An alle Channels senden
        successful, failed = await self._send_to_all_channels(embed, message.channel.id)
        
        logger.info(
            f"📤 GlobalChat: {message.author} ({message.author.id}) | "
            f"✅ {successful} erfolgreich | ❌ {failed} fehlgeschlagen"
        )
    
    # ==================== Slash Commands ====================
    
    globalchat = SlashCommandGroup("globalchat", "GlobalChat Verwaltung")
    
    @globalchat.command(
        name="setup",
        description="Richtet einen GlobalChat-Channel ein"
    )
    async def setup_globalchat(
        self,
        ctx: discord.ApplicationContext,
        channel: Option(discord.TextChannel, "Der GlobalChat-Channel", required=True)
    ):
        """Setup-Command für GlobalChat"""
        # Permissions prüfen
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(
                "❌ Du benötigst die **Server verwalten** Berechtigung!",
                ephemeral=True
            )
            return
        
        # Bot Permissions prüfen
        bot_perms = channel.permissions_for(ctx.guild.me)
        missing_perms = []
        
        if not bot_perms.send_messages:
            missing_perms.append("Nachrichten senden")
        if not bot_perms.manage_messages:
            missing_perms.append("Nachrichten verwalten")
        if not bot_perms.embed_links:
            missing_perms.append("Links einbetten")
        if not bot_perms.read_message_history:
            missing_perms.append("Nachrichtenverlauf lesen")
        
        if missing_perms:
            await ctx.respond(
                f"❌ Der Bot benötigt folgende Berechtigungen in {channel.mention}:\n"
                + "\n".join(f"• {perm}" for perm in missing_perms),
                ephemeral=True
            )
            return
        
        # Prüfen ob Channel bereits existiert
        existing_channel = db.get_globalchat_channel(ctx.guild.id)
        if existing_channel:
            await ctx.respond(
                f"⚠️ Dieser Server nutzt bereits <#{existing_channel}> als GlobalChat-Channel.\n"
                "Nutze `/globalchat remove` um ihn zu entfernen.",
                ephemeral=True
            )
            return
        
        # Channel einrichten
        try:
            success = db.set_globalchat_channel(
                ctx.guild.id,
                channel.id,
                ctx.guild.name,
                channel.name
            )
            
            if not success:
                await ctx.respond("❌ Fehler beim Einrichten!", ephemeral=True)
                return
            
            # Cache invalidieren
            self._invalidate_cache()
            
            # Willkommensnachricht im Channel
            welcome_embed = discord.Embed(
                title="🌍 GlobalChat aktiviert!",
                description=(
                    "Dieser Channel ist jetzt mit dem GlobalChat-Netzwerk verbunden.\n\n"
                    "**So funktioniert's:**\n"
                    "• Nachrichten hier werden an alle verbundenen Server gesendet\n"
                    "• Deine Nachricht wird gelöscht und als Embed neu gesendet\n"
                    "• Rate-Limit: 5 Nachrichten pro Minute\n\n"
                    "**Regeln:**\n"
                    "• Keine Discord-Invites\n"
                    "• Keine NSFW-Inhalte\n"
                    "• Respektvoller Umgang\n\n"
                    "*Viel Spaß beim Chatten! 🎉*"
                ),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            welcome_embed.set_footer(text=f"Eingerichtet von {ctx.author}", icon_url=ctx.author.display_avatar.url)
            
            try:
                await channel.send(embed=welcome_embed)
            except:
                pass
            
            # Response an Admin
            container = Container()
            container.add_text("## ✅ GlobalChat eingerichtet!")
            container.add_separator()
            container.add_text(
                f"Der Channel {channel.mention} wurde erfolgreich eingerichtet.\n\n"
                "**Nächste Schritte:**\n"
                "• `/globalchat settings` - Einstellungen anpassen\n"
                "• `/globalchat stats` - Statistiken anzeigen\n\n"
                f"**Aktuell verbunden:** {len(await self._get_cached_channels())} Server"
            )
            
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"❌ Setup-Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Ein Fehler ist aufgetreten!", ephemeral=True)
    
    @globalchat.command(
        name="remove",
        description="Entfernt den GlobalChat-Channel"
    )
    async def remove_globalchat(self, ctx: discord.ApplicationContext):
        """Entfernt GlobalChat vom Server"""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(
                "❌ Du benötigst die **Server verwalten** Berechtigung!",
                ephemeral=True
            )
            return
        
        # Prüfen ob Channel existiert
        channel_id = db.get_globalchat_channel(ctx.guild.id)
        if not channel_id:
            await ctx.respond(
                "❌ Dieser Server nutzt GlobalChat nicht!",
                ephemeral=True
            )
            return
        
        # Entfernen
        success = db.remove_globalchat_channel(ctx.guild.id)
        
        if success:
            self._invalidate_cache()
            
            container = Container()
            container.add_text("## 🗑️ GlobalChat entfernt")
            container.add_separator()
            container.add_text(
                f"Der GlobalChat-Channel <#{channel_id}> wurde entfernt.\n\n"
                "Du kannst jederzeit `/globalchat setup` nutzen, um ihn erneut einzurichten."
            )
            
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
        else:
            await ctx.respond("❌ Fehler beim Entfernen!", ephemeral=True)
    
    @globalchat.command(
        name="stats",
        description="Zeigt GlobalChat-Statistiken"
    )
    async def globalchat_stats(self, ctx: discord.ApplicationContext):
        """Zeigt umfassende Statistiken"""
        await ctx.defer()
        
        try:
            stats = db.get_global_stats()
            
            if not stats:
                await ctx.respond("❌ Fehler beim Laden der Statistiken!", ephemeral=True)
                return
            
            # Embed erstellen
            embed = discord.Embed(
                title="🌍 GlobalChat Statistiken",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Server & Nachrichten
            embed.add_field(
                name="📊 Netzwerk",
                value=(
                    f"**Aktive Server:** {stats.get('active_guilds', 0):,}\n"
                    f"**Nachrichten gesamt:** {stats.get('total_messages', 0):,}\n"
                    f"**Nachrichten heute:** {stats.get('today_messages', 0):,}"
                ),
                inline=True
            )
            
            # Moderation
            embed.add_field(
                name="🔨 Moderation",
                value=(
                    f"**Gebannte User:** {stats.get('banned_users', 0):,}\n"
                    f"**Gebannte Server:** {stats.get('banned_guilds', 0):,}"
                ),
                inline=True
            )
            
            # Dieser Server
            channel_id = db.get_globalchat_channel(ctx.guild.id)
            if channel_id:
                embed.add_field(
                    name="📍 Dieser Server",
                    value=(
                        f"**Channel:** <#{channel_id}>\n"
                        f"**Status:** ✅ Aktiv"
                    ),
                    inline=False
                )
            else:
                embed.add_field(
                    name="📍 Dieser Server",
                    value="**Status:** ❌ Nicht verbunden",
                    inline=False
                )
            
            embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.display_avatar.url)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ Stats-Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Fehler beim Laden der Statistiken!", ephemeral=True)
    
    @globalchat.command(
        name="settings",
        description="Konfiguriert GlobalChat-Einstellungen"
    )
    async def globalchat_settings(
        self,
        ctx: discord.ApplicationContext,
        filter_enabled: Option(bool, "Content-Filter aktivieren", required=False),
        nsfw_filter: Option(bool, "NSFW-Filter aktivieren", required=False),
        embed_color: Option(str, "Embed-Farbe (Hex, z.B. #FF0000)", required=False),
        max_message_length: Option(
            int,
            "Maximale Nachrichtenlänge",
            required=False,
            min_value=50,
            max_value=2000
        )
    ):
        """Verwaltet Server-spezifische Einstellungen"""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(
                "❌ Du benötigst die **Server verwalten** Berechtigung!",
                ephemeral=True
            )
            return
        
        # Prüfen ob GlobalChat aktiv
        if not db.get_globalchat_channel(ctx.guild.id):
            await ctx.respond(
                "❌ Dieser Server nutzt GlobalChat nicht!\n"
                "Nutze `/globalchat setup` zuerst.",
                ephemeral=True
            )
            return
        
        updated = []
        
        # Filter aktivieren/deaktivieren
        if filter_enabled is not None:
            if db.update_guild_setting(ctx.guild.id, 'filter_enabled', filter_enabled):
                updated.append(f"Content-Filter: {'✅ An' if filter_enabled else '❌ Aus'}")
        
        if nsfw_filter is not None:
            if db.update_guild_setting(ctx.guild.id, 'nsfw_filter', nsfw_filter):
                updated.append(f"NSFW-Filter: {'✅ An' if nsfw_filter else '❌ Aus'}")
        
        if embed_color:
            # Hex-Validierung
            if not re.match(r'^#[0-9a-fA-F]{6}$', embed_color):
                await ctx.respond(
                    "❌ Ungültiger Hex-Farbcode!\n"
                    "**Format:** `#RRGGBB` (z.B. `#FF5733`)",
                    ephemeral=True
                )
                return
            
            if db.update_guild_setting(ctx.guild.id, 'embed_color', embed_color):
                updated.append(f"Embed-Farbe: {embed_color}")
        
        if max_message_length:
            if db.update_guild_setting(ctx.guild.id, 'max_message_length', max_message_length):
                updated.append(f"Max. Länge: {max_message_length} Zeichen")
        
        # Response
        if updated:
            embed = discord.Embed(
                title="⚙️ Einstellungen aktualisiert",
                description="\n".join(f"• {setting}" for setting in updated),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Aktualisiert von {ctx.author}", icon_url=ctx.author.display_avatar.url)
        else:
            # Aktuelle Einstellungen anzeigen
            settings = db.get_guild_settings(ctx.guild.id)
            
            embed = discord.Embed(
                title="⚙️ Aktuelle Einstellungen",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🛡️ Filter",
                value=(
                    f"**Content-Filter:** {'✅ An' if settings.get('filter_enabled', True) else '❌ Aus'}\n"
                    f"**NSFW-Filter:** {'✅ An' if settings.get('nsfw_filter', True) else '❌ Aus'}"
                ),
                inline=True
            )
            
            embed.add_field(
                name="📏 Limits",
                value=f"**Max. Länge:** {settings.get('max_message_length', 1900)} Zeichen",
                inline=True
            )
            
            embed.add_field(
                name="🎨 Design",
                value=f"**Farbe:** {settings.get('embed_color', '#5865F2')}",
                inline=True
            )
            
            embed.set_footer(
                text="Nutze die Parameter um Einstellungen zu ändern",
                icon_url=ctx.author.display_avatar.url
            )
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    # ==================== Admin Commands ====================
    
    @globalchat.command(
        name="ban",
        description="[ADMIN] Sperrt einen User oder Server"
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
        # Nur Bot Owner
        if ctx.author.id not in self.config.BOT_OWNERS:
            await ctx.respond(
                "❌ Nur Bot-Owner können diesen Command nutzen!",
                ephemeral=True
            )
            return
        
        # ID validieren
        try:
            entity_id_int = int(entity_id)
        except ValueError:
            await ctx.respond("❌ Ungültige ID! Muss eine Zahl sein.", ephemeral=True)
            return
        
        # Eigenen Bot nicht bannen
        if entity_id_int == self.bot.user.id:
            await ctx.respond("❌ Du kannst den Bot nicht selbst bannen!", ephemeral=True)
            return
        
        # Owner nicht bannen
        if entity_id_int in self.config.BOT_OWNERS:
            await ctx.respond("❌ Bot-Owner können nicht gebannt werden!", ephemeral=True)
            return
        
        # Ban ausführen
        try:
            success = db.add_to_blacklist(
                entity_type,
                entity_id_int,
                reason,
                ctx.author.id,
                duration
            )
            
            if not success:
                await ctx.respond("❌ Fehler beim Bannen!", ephemeral=True)
                return
            
            # Success-Response
            duration_text = f"{duration} Stunden" if duration else "Permanent"
            
            embed = discord.Embed(
                title="🔨 GlobalChat-Ban verhängt",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Typ", value=entity_type.title(), inline=True)
            embed.add_field(name="ID", value=f"`{entity_id_int}`", inline=True)
            embed.add_field(name="Dauer", value=duration_text, inline=True)
            embed.add_field(name="Grund", value=reason, inline=False)
            embed.add_field(name="Von", value=ctx.author.mention, inline=True)
            
            if duration:
                expires = datetime.utcnow() + timedelta(hours=duration)
                embed.add_field(
                    name="Läuft ab",
                    value=f"<t:{int(expires.timestamp())}:R>",
                    inline=True
                )
            
            await ctx.respond(embed=embed)
            
            logger.info(
                f"🔨 Ban: {entity_type} {entity_id_int} | "
                f"Grund: {reason} | Von: {ctx.author} | Dauer: {duration_text}"
            )
            
        except Exception as e:
            logger.error(f"❌ Ban-Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Ein Fehler ist aufgetreten!", ephemeral=True)
    
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
        # Nur Bot Owner
        if ctx.author.id not in self.config.BOT_OWNERS:
            await ctx.respond(
                "❌ Nur Bot-Owner können diesen Command nutzen!",
                ephemeral=True
            )
            return
        
        # ID validieren
        try:
            entity_id_int = int(entity_id)
        except ValueError:
            await ctx.respond("❌ Ungültige ID! Muss eine Zahl sein.", ephemeral=True)
            return
        
        # Unban ausführen
        try:
            success = db.remove_from_blacklist(entity_type, entity_id_int)
            
            if not success:
                await ctx.respond(
                    "❌ Keine Sperre für diese ID gefunden!",
                    ephemeral=True
                )
                return
            
            # Success-Response
            embed = discord.Embed(
                title="✅ GlobalChat-Ban aufgehoben",
                description=f"{entity_type.title()} `{entity_id_int}` wurde entsperrt.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Von", value=ctx.author.mention, inline=True)
            
            await ctx.respond(embed=embed)
            
            logger.info(
                f"✅ Unban: {entity_type} {entity_id_int} | Von: {ctx.author}"
            )
            
        except Exception as e:
            logger.error(f"❌ Unban-Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Ein Fehler ist aufgetreten!", ephemeral=True)
    
    @globalchat.command(
        name="banlist",
        description="[ADMIN] Zeigt die Banliste"
    )
    async def globalchat_banlist(
        self,
        ctx: discord.ApplicationContext,
        entity_type: Option(str, "Filter", choices=["user", "guild", "all"], default="all")
    ):
        """Zeigt alle aktuellen Bans"""
        # Nur Bot Owner
        if ctx.author.id not in self.config.BOT_OWNERS:
            await ctx.respond(
                "❌ Nur Bot-Owner können diesen Command nutzen!",
                ephemeral=True
            )
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            # Stats abrufen
            stats = db.get_global_stats()
            
            embed = discord.Embed(
                title="📋 GlobalChat Banliste",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            if entity_type in ["user", "all"]:
                banned_users = stats.get('banned_users', 0)
                embed.add_field(
                    name="👤 Gebannte User",
                    value=f"**Gesamt:** {banned_users:,}",
                    inline=True
                )
            
            if entity_type in ["guild", "all"]:
                banned_guilds = stats.get('banned_guilds', 0)
                embed.add_field(
                    name="🏰 Gebannte Server",
                    value=f"**Gesamt:** {banned_guilds:,}",
                    inline=True
                )
            
            embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.display_avatar.url)
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"❌ Banlist-Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Fehler beim Laden der Banliste!", ephemeral=True)
    
    @globalchat.command(
        name="info",
        description="Zeigt Informationen über den GlobalChat"
    )
    async def globalchat_info(self, ctx: discord.ApplicationContext):
        """Zeigt allgemeine Informationen"""
        embed = discord.Embed(
            title="🌍 GlobalChat",
            description=(
                "Ein serverübergreifendes Chat-System, das Server miteinander verbindet.\n\n"
                "**Features:**\n"
                "• Nachrichten werden an alle verbundenen Server gesendet\n"
                "• Automatische Moderation und Filter\n"
                "• Rate-Limiting gegen Spam\n"
                "• Individuelle Server-Einstellungen\n\n"
                "**Wie nutze ich GlobalChat?**\n"
                "1. `/globalchat setup` - Channel einrichten\n"
                "2. In diesem Channel chatten\n"
                "3. Deine Nachricht erscheint auf allen Servern\n\n"
                "**Regeln:**\n"
                "• Keine Discord-Invites oder Werbung\n"
                "• Keine NSFW-Inhalte\n"
                "• Respektvoller Umgang\n"
                "• Max. 5 Nachrichten pro Minute"
            ),
            color=discord.Color.blue()
        )
        
        # Statistiken hinzufügen
        try:
            stats = db.get_global_stats()
            embed.add_field(
                name="📊 Netzwerk",
                value=(
                    f"**Server:** {stats.get('active_guilds', 0):,}\n"
                    f"**Nachrichten:** {stats.get('total_messages', 0):,}"
                ),
                inline=True
            )
        except:
            pass
        
        embed.set_footer(text="© 2025 OPPRO.NET Network")
        
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    """Setup-Funktion für den Bot"""
    bot.add_cog(GlobalChat(bot))