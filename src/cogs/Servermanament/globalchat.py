# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord.ext import commands, tasks
from discord import slash_command, Option, SlashCommandGroup
from src.DevTools.backend.database.globalchat_db import GlobalChatDatabase
db = GlobalChatDatabase()
import asyncio
import logging
import re
import time
from typing import List, Optional, Dict, Tuple
import aiohttp
import io
import json
from datetime import datetime, timedelta
import ezcord
from collections import defaultdict
from discord.ui import Container

# Logger konfigurieren
logger = logging.getLogger(__name__)


class GlobalChatConfig:
    """Zentrale Konfiguration für GlobalChat"""
    RATE_LIMIT_MESSAGES = 15
    RATE_LIMIT_SECONDS = 60
    CACHE_DURATION = 180  # 3 Minuten
    CLEANUP_DAYS = 30
    MIN_MESSAGE_LENGTH = 0  # Erlaube Nachrichten ohne Text (nur Medien)
    DEFAULT_MAX_MESSAGE_LENGTH = 1900
    DEFAULT_EMBED_COLOR = '#5865F2'
    
    # Medien-Limits
    MAX_FILE_SIZE_MB = 25  # Discord-Standard
    MAX_ATTACHMENTS = 10
    ALLOWED_IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']
    ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'webm', 'avi', 'mkv']
    ALLOWED_AUDIO_FORMATS = ['mp3', 'wav', 'ogg', 'm4a', 'flac']
    ALLOWED_DOCUMENT_FORMATS = ['pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z']
    
    # Bot Owner IDs
    BOT_OWNERS = [1093555256689959005, 1427994077332373554]
    
    # Content Filter Patterns
    DISCORD_INVITE_PATTERN = r'(?i)\b(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[a-zA-Z0-9]+\b'
    URL_PATTERN = r'(?i)\bhttps?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F]{2}))+\b'
    
    # NSFW Keywords
    NSFW_KEYWORDS = [
        'nsfw', 'porn', 'sex', 'xxx', 'nude', 'hentai', 
        'dick', 'pussy', 'cock', 'tits', 'ass', 'fuck'
    ]


class MediaHandler:
    """Verarbeitet alle Arten von Medien und Anhängen"""
    
    def __init__(self, config: GlobalChatConfig):
        self.config = config
    
    def validate_attachments(self, attachments: List[discord.Attachment]) -> Tuple[bool, str, List[discord.Attachment]]:
        """Validiert Attachments und gibt valide zurück"""
        if not attachments:
            return True, "", []
        
        if len(attachments) > self.config.MAX_ATTACHMENTS:
            return False, f"Zu viele Anhänge (max. {self.config.MAX_ATTACHMENTS})", []
        
        valid_attachments = []
        max_size_bytes = self.config.MAX_FILE_SIZE_MB * 1024 * 1024
        
        for attachment in attachments:
            # Größe prüfen
            if attachment.size > max_size_bytes:
                return False, f"Datei '{attachment.filename}' ist zu groß (max. {self.config.MAX_FILE_SIZE_MB}MB)", []
            
            # Dateiformat prüfen
            file_ext = attachment.filename.split('.')[-1].lower() if '.' in attachment.filename else ''
            
            all_allowed = (
                self.config.ALLOWED_IMAGE_FORMATS +
                self.config.ALLOWED_VIDEO_FORMATS +
                self.config.ALLOWED_AUDIO_FORMATS +
                self.config.ALLOWED_DOCUMENT_FORMATS
            )
            
            if file_ext and file_ext not in all_allowed:
                return False, f"Dateiformat '.{file_ext}' nicht erlaubt", []
            
            valid_attachments.append(attachment)
        
        return True, "", valid_attachments
    
    def categorize_attachment(self, attachment: discord.Attachment) -> str:
        """Kategorisiert einen Anhang nach Typ"""
        if not attachment.filename or '.' not in attachment.filename:
            return 'other'
        
        file_ext = attachment.filename.split('.')[-1].lower()
        
        if file_ext in self.config.ALLOWED_IMAGE_FORMATS:
            return 'image'
        elif file_ext in self.config.ALLOWED_VIDEO_FORMATS:
            return 'video'
        elif file_ext in self.config.ALLOWED_AUDIO_FORMATS:
            return 'audio'
        elif file_ext in self.config.ALLOWED_DOCUMENT_FORMATS:
            return 'document'
        else:
            return 'other'
    
    def get_attachment_icon(self, attachment: discord.Attachment) -> str:
        """Gibt passendes Icon für Attachment-Typ zurück"""
        category = self.categorize_attachment(attachment)
        
        icons = {
            'image': '🖼️',
            'video': '🎥',
            'audio': '🎵',
            'document': '📄',
            'other': '📎'
        }
        
        return icons.get(category, '📎')
    
    def format_file_size(self, size_bytes: int) -> str:
        """Formatiert Dateigröße leserlich"""
        for unit in ['B', 'KB', 'MB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} GB"


class MessageValidator:
    """Validiert und filtert Nachrichten"""
    
    def __init__(self, config: GlobalChatConfig):
        self.config = config
        self.media_handler = MediaHandler(config)
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
        
        # Leere Nachrichten (ohne Text UND ohne Anhänge/Sticker)
        if not message.content and not message.attachments and not message.stickers:
            return False, "Leere Nachricht"
        
        # Nachrichtenlänge (nur wenn Text vorhanden)
        if message.content:
            content_length = len(message.content.strip())
            
            # Mindestlänge nur bei reinen Text-Nachrichten
            if content_length < self.config.MIN_MESSAGE_LENGTH and not message.attachments and not message.stickers:
                return False, "Zu kurze Nachricht"
            
            max_length = settings.get('max_message_length', self.config.DEFAULT_MAX_MESSAGE_LENGTH)
            if content_length > max_length:
                return False, f"Nachricht zu lang (max. {max_length} Zeichen)"
        
        # Attachments validieren
        if message.attachments:
            valid, reason, _ = self.media_handler.validate_attachments(message.attachments)
            if not valid:
                return False, f"Ungültige Anhänge: {reason}"
        
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
        
        return False, ""
    
    def check_nsfw_content(self, content: str) -> bool:
        """Erweiterte NSFW-Erkennung"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # Keyword-Check mit Wortgrenzen
        for keyword in self.config.NSFW_KEYWORDS:
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
    """Erstellt formatierte Embeds für GlobalChat mit vollständigem Medien-Support"""
    
    def __init__(self, config: GlobalChatConfig, bot=None):
        self.config = config
        self.media_handler = MediaHandler(config)
        self.bot = bot  # Bot für Message-Fetching
    
    async def create_message_embed(self, message: discord.Message, settings: Dict, attachment_data: List[Tuple[str, bytes, str]] = None) -> Tuple[discord.Embed, List[Tuple[str, bytes]]]:
        """Erstellt ein verbessertes Embed mit vollständigem Medien-Support
        
        attachment_data: Liste von (filename, bytes, content_type) - schon heruntergeladene Dateien
        Gibt (embed, [(filename, bytes), ...]) zurück - Bytes statt discord.File!
        """
        if attachment_data is None:
            attachment_data = []
        
        content = self._clean_content(message.content)
        
        # Embed-Farbe
        embed_color = self._parse_color(settings.get('embed_color', self.config.DEFAULT_EMBED_COLOR))
        
        # Beschreibung
        if content:
            description = content
        elif message.attachments or message.stickers or attachment_data:
            description = "*Medien-Nachricht*"
        else:
            description = "*Keine Beschreibung*"
        
        # Embed erstellen
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
        
        # Footer mit Server-Info UND Original-Message-ID (für Reply-Tracking)
        footer_text = f"📍 {message.guild.name} • #{message.channel.name} • ID:{message.id}"
        embed.set_footer(
            text=footer_text,
            icon_url=message.guild.icon.url if message.guild.icon else None
        )
        
        # Reply-Kontext hinzufügen (robust, ohne invasive Änderungen)
        if message.reference:
            try:
                # Versuche zuerst die gecachte referenzierte Nachricht
                replied_msg = message.reference.resolved

                # Falls nicht im Cache, versuche die referenzierte Nachricht aus dem referenzierten Kanal zu holen
                if not replied_msg and getattr(message.reference, 'message_id', None):
                    ref_channel = None
                    ref_chan_id = getattr(message.reference, 'channel_id', None)
                    if ref_chan_id:
                        # Versuche zuerst den Kanal vom Bot-Cache
                        ref_channel = self.bot.get_channel(ref_chan_id)
                        # Fallback auf Guild-Kanal
                        if not ref_channel and message.guild:
                            try:
                                ref_channel = message.guild.get_channel(ref_chan_id)
                            except Exception:
                                ref_channel = None
                    if not ref_channel:
                        ref_channel = message.channel

                    if ref_channel:
                        try:
                            replied_msg = await ref_channel.fetch_message(message.reference.message_id)
                        except Exception:
                            replied_msg = None

                # Wenn wir eine referenzierte Nachricht haben, bereite Vorschau vor
                if isinstance(replied_msg, discord.Message):
                    # Text-Vorschau (bevorzuge echten content)
                    preview = replied_msg.content or ""

                    # Wenn die referenzierte Nachricht das Relay-Bot-Embed ist, versuche Text aus dem Embed
                    if not preview and replied_msg.embeds:
                        try:
                            preview = replied_msg.embeds[0].description or ""
                        except Exception:
                            preview = ""

                    # Fallback auf Anhänge/Sticker
                    if not preview:
                        if replied_msg.attachments:
                            preview = f"📎 {len(replied_msg.attachments)} Datei(en)"
                        elif replied_msg.stickers:
                            preview = "🎨 Sticker"
                        else:
                            preview = "*(Leere Nachricht)*"

                    preview = self._clean_content(preview)
                    preview_short = (preview[:200] + "...") if len(preview) > 200 else preview

                    # Author bestimmen: falls die referenzierte Nachricht vom Bot ist, versuche embed.author
                    author_display = None
                    try:
                        if replied_msg.author and replied_msg.author.id == getattr(self.bot, 'user', None).id and replied_msg.embeds:
                            emb = replied_msg.embeds[0]
                            if emb.author and emb.author.name:
                                author_display = emb.author.name
                    except Exception:
                        author_display = None

                    if not author_display:
                        try:
                            author_display = replied_msg.author.display_name
                        except Exception:
                            author_display = "Unbekannter User"

                    # Herkunft (Server • #channel)
                    origin = None
                    try:
                        if getattr(replied_msg, 'guild', None) and getattr(replied_msg, 'channel', None):
                            origin = f"{replied_msg.guild.name} • #{replied_msg.channel.name}"
                    except Exception:
                        origin = None

                    reply_field = f"**{author_display}:** {preview_short}"
                    if origin:
                        reply_field += f"\n_{origin}_"

                    embed.add_field(name="↩️ Antwort (Vorschau)", value=reply_field, inline=False)
            except Exception:
                # Never fail building the embed just because reply resolution failed
                pass
        
        # Medien verarbeiten mit heruntergeladenen Dateien
        files_to_upload = await self._process_media(embed, message, attachment_data)

        # Rückgabe: Embed + Liste von discord.File Objekten
        return embed, files_to_upload
    
    async def _process_media(self, embed: discord.Embed, message: discord.Message, attachment_data: List[Tuple[str, bytes, str]] = None) -> List[Tuple[str, bytes]]:
        """Verarbeitet alle Medien-Typen mit heruntergeladenen Anhängen
        
        attachment_data: Liste von (filename, bytes, content_type) - bereits heruntergeladen
        Gibt Liste von (filename, bytes) zurück - NOT discord.File!
        """
        if attachment_data is None:
            attachment_data = []
        
        attachment_bytes: List[Tuple[str, bytes]] = []

        # === HERUNTERGELADENE ATTACHMENTS ===
        if attachment_data:
            attachment_bytes.extend(self._process_downloaded_attachments(embed, attachment_data))

        # === STICKERS ===
        if message.stickers:
            self._process_stickers(embed, message.stickers)

        # === ORIGINAL EMBEDS (z.B. von Links) ===
        if message.embeds:
            self._process_embeds(embed, message.embeds)

        return attachment_bytes
    
    def _process_downloaded_attachments(self, embed: discord.Embed, attachment_data: List[Tuple[str, bytes, str]]) -> List[Tuple[str, bytes]]:
        """Verarbeitet heruntergeladene Anhänge und gibt (filename, bytes) zurück
        
        attachment_data: [(filename, bytes_data, content_type), ...]
        Gibt [(filename, bytes), ...] zurück - NICHT discord.File!
        """
        attachment_bytes: List[Tuple[str, bytes]] = []
        
        # Kategorisiere nach Typ
        images = []
        videos = []
        audios = []
        documents = []
        others = []
        
        for filename, data, content_type in attachment_data:
            # Bestimme Dateityp anhand von content_type und Dateiendung
            category = self._get_attachment_category(filename, content_type)
            
            if category == 'image':
                images.append((filename, data))
            elif category == 'video':
                videos.append((filename, data))
            elif category == 'audio':
                audios.append((filename, data))
            elif category == 'document':
                documents.append((filename, data))
            else:
                others.append((filename, data))

        # === BILDER ===
        if images:
            # Erstes Bild als Attachment für embed.set_image()
            first_name, first_data = images[0]
            embed.set_image(url=f"attachment://{first_name}")
            attachment_bytes.append((first_name, first_data))

            # Weitere Bilder
            if len(images) > 1:
                image_links = []
                for i, (img_name, img_data) in enumerate(images[1:], start=2):
                    size = len(img_data)
                    size_str = self.media_handler.format_file_size(size)
                    image_links.append(f"🖼️ {img_name} ({size_str})")
                    attachment_bytes.append((img_name, img_data))
                
                if image_links:
                    embed.add_field(
                        name="📷 Weitere Bilder",
                        value="\n".join(image_links[:5]),  # Max 5
                        inline=False
                    )

        # === VIDEOS ===
        if videos:
            video_links = []
            for video_name, video_data in videos:
                size = len(video_data)
                size_str = self.media_handler.format_file_size(size)
                video_links.append(f"🎥 {video_name} ({size_str})")
                attachment_bytes.append((video_name, video_data))
            
            if video_links:
                embed.add_field(
                    name="🎬 Videos",
                    value="\n".join(video_links[:3]),  # Max 3
                    inline=False
                )

        # === AUDIO ===
        if audios:
            audio_links = []
            for audio_name, audio_data in audios:
                size = len(audio_data)
                size_str = self.media_handler.format_file_size(size)
                audio_links.append(f"🎵 {audio_name} ({size_str})")
                attachment_bytes.append((audio_name, audio_data))
            
            if audio_links:
                embed.add_field(
                    name="🎧 Audio-Dateien",
                    value="\n".join(audio_links[:3]),  # Max 3
                    inline=False
                )

        # === DOKUMENTE ===
        if documents:
            doc_links = []
            for doc_name, doc_data in documents:
                size = len(doc_data)
                size_str = self.media_handler.format_file_size(size)
                doc_links.append(f"📄 {doc_name} ({size_str})")
                attachment_bytes.append((doc_name, doc_data))
            
            if doc_links:
                embed.add_field(
                    name="📦 Dateien",
                    value="\n".join(doc_links[:5]),  # Max 5
                    inline=False
                )

        # === SONSTIGE DATEIEN ===
        if others:
            other_links = []
            for other_name, other_data in others:
                size = len(other_data)
                size_str = self.media_handler.format_file_size(size)
                other_links.append(f"📎 {other_name} ({size_str})")
                attachment_bytes.append((other_name, other_data))
            
            if other_links:
                embed.add_field(
                    name="📎 Sonstige Dateien",
                    value="\n".join(other_links[:5]),  # Max 5
                    inline=False
                )

        return attachment_bytes
    
    def _get_attachment_category(self, filename: str, content_type: str = "") -> str:
        """Bestimmt Kategorie eines Attachments anhand Dateiname und Content-Type"""
        if not filename:
            return 'other'
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Prüfe Extension
        if file_ext in self.config.ALLOWED_IMAGE_FORMATS or 'image' in content_type.lower():
            return 'image'
        elif file_ext in self.config.ALLOWED_VIDEO_FORMATS or 'video' in content_type.lower():
            return 'video'
        elif file_ext in self.config.ALLOWED_AUDIO_FORMATS or 'audio' in content_type.lower():
            return 'audio'
        elif file_ext in self.config.ALLOWED_DOCUMENT_FORMATS or 'application' in content_type.lower():
            return 'document'
        
        return 'other'
    
    def _process_stickers(self, embed: discord.Embed, stickers: List[discord.Sticker]):
        """Verarbeitet Discord-Sticker"""
        sticker_info = []
        
        for sticker in stickers[:3]:  # Max 3 Sticker
            # Sticker-URL (wenn verfügbar)
            if sticker.url:
                sticker_info.append(f"[:{sticker.name}:]({sticker.url})")
            else:
                sticker_info.append(f":{sticker.name}:")
        
        if sticker_info:
            embed.add_field(
                name="🎨 Sticker",
                value=" • ".join(sticker_info),
                inline=False
            )
            
            # Erstes Sticker als Thumbnail (wenn verfügbar und kein Bild)
            if stickers[0].url and not embed.image:
                embed.set_thumbnail(url=stickers[0].url)
    
    def _process_embeds(self, main_embed: discord.Embed, message_embeds: List[discord.Embed]):
        """Verarbeitet Original-Embeds (z.B. von YouTube, Twitter, etc.)"""
        
        # Nur Link-Previews verarbeiten (typ: rich, link, video, image)
        link_embeds = []
        
        for emb in message_embeds[:2]:  # Max 2 Embeds
            if emb.type in ['rich', 'link', 'video', 'image', 'article']:
                
                info_parts = []
                
                # Titel
                if emb.title:
                    if emb.url:
                        info_parts.append(f"**[{emb.title}]({emb.url})**")
                    else:
                        info_parts.append(f"**{emb.title}**")
                
                # Beschreibung (gekürzt)
                if emb.description:
                    desc = emb.description[:150]
                    if len(emb.description) > 150:
                        desc += "..."
                    info_parts.append(desc)
                
                # Provider (z.B. YouTube, Twitter)
                if emb.provider:
                    info_parts.append(f"*via {emb.provider.name}*")
                
                if info_parts:
                    link_embeds.append("\n".join(info_parts))
        
        if link_embeds:
            main_embed.add_field(
                name="🔗 Verlinkte Inhalte",
                value="\n\n".join(link_embeds),
                inline=False
            )
    
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
        
        # Account-Alter Badge
        account_age = (datetime.now(author.created_at.tzinfo) - author.created_at).days
        if account_age < 30:
            badges.append("🆕")
        
        # Author-Text zusammenbauen
        badge_str = ''.join(badges) + ' ' if badges else ''
        author_text = f"{badge_str}{author.display_name}"
        
        if roles:
            author_text += f" • {' | '.join(roles)}"
        
        return author_text, badges


class GlobalChat(ezcord.Cog, group="globalchat"):
    """Hauptklasse für GlobalChat-Funktionalität mit vollständigem Medien-Support"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = GlobalChatConfig()
        self.validator = MessageValidator(self.config)
        self.embed_builder = EmbedBuilder(self.config, bot)  # Bot mitgeben!
        self.media_handler = MediaHandler(self.config)
        
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
    
    async def _send_to_channel(self, channel_id: int, embed: discord.Embed, attachment_bytes: Optional[List[Tuple[str, bytes]]] = None) -> bool:
        """Sendet Embed an spezifischen Channel mit Error-Handling
        
        attachment_bytes: Liste von (filename, bytes) - wird zu discord.File konvertiert
                         Wichtig: Raw bytes, nicht discord.File, da File-Streams verbraucht sind!
        """
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"⚠️ Channel {channel_id} nicht gefunden")
                return False
            
            # Permissions prüfen
            perms = channel.permissions_for(channel.guild.me)
            if not perms.send_messages or not perms.embed_links:
                logger.warning(f"⚠️ Keine Permissions in {channel_id}")
                return False
            
            # Erstelle NEUE discord.File Objekte für diesen Channel (wichtig!)
            # Jeder Channel bekommt seine eigenen frischen Files!
            files = []
            if attachment_bytes:
                for filename, data in attachment_bytes:
                    try:
                        files.append(discord.File(io.BytesIO(data), filename=filename))
                    except Exception as e:
                        logger.warning(f"⚠️ Error creating file {filename}: {e}")
            
            # Sende mit Retry-Logik
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if files:
                        await channel.send(embed=embed, files=files)
                    else:
                        await channel.send(embed=embed)
                    return True
                except (ConnectionResetError, asyncio.TimeoutError, OSError) as net_err:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Netzwerk-Fehler in {channel_id}, Versuch {attempt + 1}/{max_retries}: {net_err}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    else:
                        logger.error(f"❌ Netzwerk-Fehler in {channel_id} nach {max_retries} Versuchen: {net_err}")
                        return False
            
            return True
            
        except discord.Forbidden:
            logger.warning(f"⚠️ Forbidden in Channel {channel_id}")
            return False
        except discord.HTTPException as e:
            if e.status == 429:  # Rate Limited
                logger.warning(f"⚠️ Rate Limited in Channel {channel_id}")
                await asyncio.sleep(5)  # Warte länger bei Rate Limit
            else:
                logger.error(f"❌ HTTP Error {e.status} in Channel {channel_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unbekannter Fehler in Channel {channel_id}: {type(e).__name__}: {e}")
            return False
    
    async def _send_to_all_channels(self, embed: discord.Embed, source_channel_id: int, attachment_bytes: Optional[List[Tuple[str, bytes]]] = None) -> Tuple[int, int]:
        """Sendet Embed an alle GlobalChat-Channels (parallel)
        
        attachment_bytes: Liste von (filename, bytes) - wird für jeden Channel neu zu discord.File konvertiert
        """
        channel_ids = await self._get_cached_channels()

        # Erstelle Tasks für paralleles Senden
        tasks = [
            self._send_to_channel(channel_id, embed, attachment_bytes)
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
        """Hauptlogik für GlobalChat-Nachrichten mit vollständigem Medien-Support"""
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
            
            # User benachrichtigen bei bestimmten Gründen
            if any(keyword in reason for keyword in ["Blacklist", "NSFW", "Gefilterte", "Ungültige Anhänge", "zu groß"]):
                try:
                    await message.add_reaction("❌")
                    
                    # Info-Nachricht für spezifische Fehler
                    if "Ungültige Anhänge" in reason or "zu groß" in reason:
                        info_msg = await message.reply(
                            f"❌ **Fehler:** {reason}\n"
                            f"**Max. Größe:** {self.config.MAX_FILE_SIZE_MB}MB pro Datei\n"
                            f"**Max. Anhänge:** {self.config.MAX_ATTACHMENTS}",
                            delete_after=7
                        )
                    
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
        
        # ✅ ZUERST: Anhänge herunterladen BEVOR Nachricht gelöscht wird (URLs ablaufen sonst!)
        attachment_data = []
        if message.attachments:
            try:
                # Timeout für größere Dateien - aber viel kürzer (30s total)
                timeout = aiohttp.ClientTimeout(total=30, sock_connect=5, sock_read=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    for att in message.attachments:
                        try:
                            async with session.get(att.url, ssl=False) as resp:
                                if resp.status == 200:
                                    data = await resp.read()
                                    # Speichere als raw bytes, nicht als BytesIO!
                                    attachment_data.append((att.filename, data, att.content_type))
                                    logger.debug(f"✅ Downloaded: {att.filename} ({len(data)} bytes)")
                                else:
                                    logger.warning(f"⚠️ Download failed for {att.filename}: Status {resp.status}")
                        except (asyncio.TimeoutError, asyncio.CancelledError) as te:
                            logger.warning(f"⏱️ Timeout downloading {att.filename}: {te}")
                        except (aiohttp.ClientOSError, aiohttp.ClientConnectionError) as ce:
                            logger.warning(f"⚠️ Connection error downloading {att.filename}: {ce}")
                        except Exception as e:
                            logger.error(f"❌ Error downloading {att.filename}: {type(e).__name__}: {e}")
            except Exception as e:
                logger.error(f"❌ Error in attachment download session: {type(e).__name__}: {e}")
        
        # Message loggen (inkl. Attachments)
        try:
            attachment_urls = [att.url for att in message.attachments] if message.attachments else None
            attachment_str = ",".join(attachment_urls) if attachment_urls else None
            
            db.log_message(
                message.author.id,
                message.guild.id,
                message.channel.id,
                message.content,
                attachment_str
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
            return
        except discord.NotFound:
            pass
        
        # Embed erstellen mit heruntergeladenen Dateien
        try:
            embed, files = await self.embed_builder.create_message_embed(message, settings, attachment_data)
        except Exception as e:
            logger.error(f"❌ Fehler beim Embed-Erstellen: {e}", exc_info=True)
            return

        # An alle Channels senden (inkl. Dateien)
        successful, failed = await self._send_to_all_channels(embed, message.channel.id, files)
        
        # Log-Info erstellen
        media_info = ""
        if message.attachments:
            media_info = f"📎 {len(message.attachments)} Anhänge"
        if message.stickers:
            if media_info:
                media_info += f" | 🎨 {len(message.stickers)} Sticker"
            else:
                media_info = f"🎨 {len(message.stickers)} Sticker"
        
    
    # ==================== Slash Commands ====================
    
    globalchat = SlashCommandGroup("globalchat", "GlobalChat Verwaltung")
    
    @globalchat.command(
        name="setup",
        description="Richtet einen GlobalChat-Channel ein"
    )
    async def setup_globalchat(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel = Option(discord.TextChannel, "Der GlobalChat-Channel", required=True)
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
        if not bot_perms.attach_files:
            missing_perms.append("Dateien anhängen")
        
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
                    "**Unterstützte Medien:**\n"
                    "• 🖼️ Bilder (PNG, JPG, GIF, WebP, BMP)\n"
                    "• 🎥 Videos (MP4, MOV, WebM, AVI, MKV)\n"
                    "• 🎵 Audio (MP3, WAV, OGG, M4A, FLAC)\n"
                    "• 📄 Dokumente (PDF, Office-Dateien, Archive)\n"
                    "• 🎨 Discord Sticker\n"
                    "• 🔗 Link-Previews (YouTube, Twitter, etc.)\n"
                    "• ↩️ Antworten auf Nachrichten\n\n"
                    "**Regeln:**\n"
                    "• Keine Discord-Invites\n"
                    "• Keine NSFW-Inhalte\n"
                    "• Max. 25MB pro Datei\n"
                    "• Max. 10 Anhänge pro Nachricht\n"
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
                "**Features:**\n"
                "• 📝 Text-Nachrichten mit Formatierung\n"
                "• 🖼️ Bilder (automatische Anzeige)\n"
                "• 🎥 Videos (Download-Links)\n"
                "• 🎵 Audio-Dateien\n"
                "• 📄 Dokumente (Office, PDF, Archive)\n"
                "• 🎨 Discord Sticker\n"
                "• 🔗 Automatische Link-Previews\n"
                "• ↩️ Reply auf andere Nachrichten\n\n"
                "**Nächste Schritte:**\n"
                "• `/globalchat settings` - Einstellungen anpassen\n"
                "• `/globalchat stats` - Statistiken anzeigen\n"
                "• `/globalchat media-info` - Medien-Limits anzeigen\n\n"
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
            
            # Medien-Support Info
            embed.add_field(
                name="📁 Medien-Support",
                value=(
                    "✅ Bilder & Videos\n"
                    "✅ Audio & Dokumente\n"
                    "✅ Sticker & Links\n"
                    "✅ Reply-Support"
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
        filter_enabled: Optional[bool] = Option(bool, "Content-Filter aktivieren", required=False),
        nsfw_filter: Optional[bool] = Option(bool, "NSFW-Filter aktivieren", required=False),
        embed_color: Optional[str] = Option(str, "Embed-Farbe (Hex, z.B. #FF0000)", required=False),
        max_message_length: Optional[int] = Option(
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
        
    
    # ==================== Admin Commands ====================
    
    @globalchat.command(
        name="ban",
        description="[ADMIN] Sperrt einen User oder Server vom GlobalChat"
    )
    async def ban_from_globalchat(
        self,
        ctx: discord.ApplicationContext,
        entity_type: str = Option(str, "Was sperren", choices=["user", "guild"]),
        entity_id: str = Option(str, "User-ID oder Server-ID"),
        reason: str = Option(str, "Grund für die Sperre"),
        duration: Optional[int] = Option(int, "Dauer in Stunden (leer = permanent)", required=False)
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
        entity_type: str = Option(str, "Was entsperren", choices=["user", "guild"]),
        entity_id: str = Option(str, "User-ID oder Server-ID")
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
        entity_type: str = Option(str, "Filter", choices=["user", "guild", "all"], default="all")
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
            title="🌍 GlobalChat - Vollständiger Medien-Support",
            description=(
                "Ein serverübergreifendes Chat-System mit vollständigem Medien-Support.\n\n"
                "**🎯 Hauptfeatures:**\n"
                "• Nachrichten werden an alle verbundenen Server gesendet\n"
                "• Vollständiger Medien-Support (Bilder, Videos, Audio, Dokumente)\n"
                "• Discord Sticker und Link-Previews\n"
                "• Reply-Unterstützung mit Kontext\n"
                "• Automatische Moderation und Filter\n"
                "• Rate-Limiting gegen Spam\n"
                "• Individuelle Server-Einstellungen\n\n"
                "**📁 Unterstützte Medien:**\n"
                "• 🖼️ **Bilder:** PNG, JPG, GIF, WebP, BMP\n"
                "• 🎥 **Videos:** MP4, MOV, WebM, AVI, MKV\n"
                "• 🎵 **Audio:** MP3, WAV, OGG, M4A, FLAC\n"
                "• 📄 **Dokumente:** PDF, Office, Archive\n"
                "• 🎨 **Sticker:** Discord Sticker (automatisch)\n"
                "• 🔗 **Links:** YouTube, Twitter, Spotify (Preview)\n\n"
                "**🚀 Wie nutze ich GlobalChat?**\n"
                "1. `/globalchat setup` - Channel einrichten\n"
                "2. In diesem Channel chatten\n"
                "3. Medien, Sticker und mehr senden\n"
                "4. Deine Nachricht erscheint auf allen Servern\n\n"
                "**📏 Regeln & Limits:**\n"
                "• Keine Discord-Invites oder Werbung\n"
                "• Keine NSFW-Inhalte\n"
                "• Max. 25MB pro Datei (Discord-Limit)\n"
                "• Max. 10 Anhänge pro Nachricht\n"
                "• Max. 5 Nachrichten pro Minute\n"
                "• Respektvoller Umgang"
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
                    f"**Nachrichten:** {stats.get('total_messages', 0):,}\n"
                    f"**Heute:** {stats.get('today_messages', 0):,}"
                ),
                inline=True
            )
        except:
            pass
        
        # Medien-Features
        embed.add_field(
            name="✨ Features",
            value=(
                "🖼️ Bilder\n"
                "🎥 Videos\n"
                "🎵 Audio\n"
                "📄 Dokumente\n"
                "🎨 Sticker\n"
                "🔗 Link-Previews\n"
                "↩️ Replies"
            ),
            inline=True
        )
        
        # Commands
        embed.add_field(
            name="🛠️ Wichtige Commands",
            value=(
                "`/globalchat setup` - Einrichten\n"
                "`/globalchat settings` - Konfiguration\n"
                "`/globalchat media-info` - Medien-Details\n"
                "`/globalchat stats` - Statistiken\n"
                "`/globalchat test-media` - Test"
            ),
            inline=False
        )
        
        embed.set_footer(text="© 2025 OPPRO.NET Network • Vollständiger Medien-Support")
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @globalchat.command(
        name="broadcast",
        description="[ADMIN] Sendet eine Broadcast-Nachricht an alle GlobalChat-Channels"
    )
    async def broadcast(
        self,
        ctx: discord.ApplicationContext,
        title: str = Option(str, "Titel der Nachricht"),
        message: str = Option(str, "Nachricht"),
        color: str = Option(str, "Embed-Farbe (Hex)", required=False, default="#5865F2")
    ):
        """Sendet Broadcast an alle Channels (nur für Bot-Owner)"""
        # Nur Bot Owner
        if ctx.author.id not in self.config.BOT_OWNERS:
            await ctx.respond(
                "❌ Nur Bot-Owner können diesen Command nutzen!",
                ephemeral=True
            )
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            # Embed erstellen
            embed_color = self.embed_builder._parse_color(color)
            
            embed = discord.Embed(
                title=f"📢 {title}",
                description=message,
                color=embed_color,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(
                text=f"GlobalChat Broadcast von {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )
            
            # An alle Channels senden
            successful, failed = await self._send_to_all_channels(embed, 0)
            
            # Response
            result_embed = discord.Embed(
                title="✅ Broadcast gesendet",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            result_embed.add_field(
                name="📊 Ergebnis",
                value=(
                    f"**Erfolgreich:** {successful}\n"
                    f"**Fehlgeschlagen:** {failed}\n"
                    f"**Gesamt:** {successful + failed}"
                ),
                inline=False
            )
            
            result_embed.add_field(
                name="📝 Nachricht",
                value=f"**{title}**\n{message[:100]}{'...' if len(message) > 100 else ''}",
                inline=False
            )
            
            await ctx.respond(embed=result_embed, ephemeral=True)
            
            logger.info(
                f"📢 Broadcast: '{title}' | Von: {ctx.author} | "
                f"✅ {successful} | ❌ {failed}"
            )
            
        except Exception as e:
            logger.error(f"❌ Broadcast-Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Fehler beim Senden des Broadcasts!", ephemeral=True)


    # ==================== Error Handler ====================
    
    @globalchat.command(
        name="reload-cache",
        description="[ADMIN] Lädt den Channel-Cache neu"
    )
    async def reload_cache(self, ctx: discord.ApplicationContext):
        """Lädt Cache manuell neu (für Bot-Owner)"""
        if ctx.author.id not in self.config.BOT_OWNERS:
            await ctx.respond(
                "❌ Nur Bot-Owner können diesen Command nutzen!",
                ephemeral=True
            )
            return
        
        try:
            old_count = len(self._channel_cache)
            self._invalidate_cache()
            self._channel_cache = db.get_all_channels()
            self._cache_last_update = time.time()
            new_count = len(self._channel_cache)
            
            embed = discord.Embed(
                title="🔄 Cache neu geladen",
                description=f"**Vorher:** {old_count} Channels\n**Nachher:** {new_count} Channels",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            logger.info(f"🔄 Cache manuell neu geladen: {old_count} → {new_count} Channels")
            
        except Exception as e:
            logger.error(f"❌ Cache-Reload Fehler: {e}", exc_info=True)
            await ctx.respond("❌ Fehler beim Neuladen des Cache!", ephemeral=True)
    
    @globalchat.command(
        name="debug",
        description="[ADMIN] Zeigt Debug-Informationen"
    )
    async def debug_info(self, ctx: discord.ApplicationContext):
        """Zeigt Debug-Infos (für Bot-Owner)"""
        if ctx.author.id not in self.config.BOT_OWNERS:
            await ctx.respond(
                "❌ Nur Bot-Owner können diesen Command nutzen!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🐛 Debug-Informationen",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        # Cache-Info
        cache_age = time.time() - self._cache_last_update if self._cache_last_update > 0 else 0
        embed.add_field(
            name="📦 Cache",
            value=(
                f"**Channels:** {len(self._channel_cache)}\n"
                f"**Alter:** {int(cache_age)}s\n"
                f"**Letzte Aktualisierung:** <t:{int(self._cache_last_update)}:R>"
            ),
            inline=True
        )
        
        # Bot-Info
        embed.add_field(
            name="🤖 Bot",
            value=(
                f"**Guilds:** {len(self.bot.guilds)}\n"
                f"**User:** {len(self.bot.users)}\n"
                f"**Latenz:** {round(self.bot.latency * 1000)}ms"
            ),
            inline=True
        )
        
        # Tasks
        cleanup_running = self.cleanup_task.is_running()
        cache_running = self.cache_refresh_task.is_running()
        embed.add_field(
            name="⚙️ Background Tasks",
            value=(
                f"**Cleanup:** {'✅ Läuft' if cleanup_running else '❌ Gestoppt'}\n"
                f"**Cache Refresh:** {'✅ Läuft' if cache_running else '❌ Gestoppt'}"
            ),
            inline=True
        )
        
        # Config
        embed.add_field(
            name="🔧 Konfiguration",
            value=(
                f"**Rate Limit:** {self.config.RATE_LIMIT_MESSAGES}/{self.config.RATE_LIMIT_SECONDS}s\n"
                f"**Max. Attachments:** {self.config.MAX_ATTACHMENTS}\n"
                f"**Max. File Size:** {self.config.MAX_FILE_SIZE_MB}MB"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @globalchat.command(
        name="help",
        description="Zeigt eine Hilfe-Übersicht für GlobalChat"
    )
    async def help_command(self, ctx: discord.ApplicationContext):
        """Zeigt Hilfe für GlobalChat"""
        
        embed = discord.Embed(
            title="📚 GlobalChat Hilfe",
            description="Hier ist eine Übersicht aller verfügbaren Commands und Features.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Setup & Verwaltung
        embed.add_field(
            name="⚙️ Setup & Verwaltung",
            value=(
                "`/globalchat setup` - Channel einrichten\n"
                "`/globalchat remove` - Channel entfernen\n"
                "`/globalchat settings` - Einstellungen anpassen"
            ),
            inline=False
        )
        
        # Informationen
        embed.add_field(
            name="📊 Informationen",
            value=(
                "`/globalchat info` - Allgemeine Infos\n"
                "`/globalchat stats` - Statistiken anzeigen\n"
                "`/globalchat media-info` - Medien-Details\n"
                "`/globalchat help` - Diese Hilfe"
            ),
            inline=False
        )
        
        # Test & Debug
        embed.add_field(
            name="🧪 Test & Debug",
            value=(
                "`/globalchat test-media` - Medien-Test\n"
                "`/globalchat debug` - Debug-Info (Admin)\n"
                "`/globalchat reload-cache` - Cache neu laden (Admin)"
            ),
            inline=False
        )
        
        # Moderation (Admin)
        embed.add_field(
            name="🔨 Moderation (Bot-Owner)",
            value=(
                "`/globalchat ban` - User/Server sperren\n"
                "`/globalchat unban` - Sperre aufheben\n"
                "`/globalchat banlist` - Sperrliste anzeigen\n"
                "`/globalchat broadcast` - Broadcast senden"
            ),
            inline=False
        )
        
        # Features
        embed.add_field(
            name="✨ Unterstützte Features",
            value=(
                "🖼️ Bilder • 🎥 Videos • 🎵 Audio\n"
                "📄 Dokumente • 🎨 Sticker • 🔗 Links\n"
                "↩️ Antworten • 👥 User-Badges"
            ),
            inline=False
        )
        
        embed.set_footer(
            text=f"Bei Fragen wende dich an einen Bot-Owner | Angefordert von {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    
    @globalchat.command(
        name="media-info",
        description="Zeigt Informationen über unterstützte Medien"
    )
    async def media_info(self, ctx: discord.ApplicationContext):
        """Zeigt detaillierte Informationen über Medien-Support"""
        
        embed = discord.Embed(
            title="📁 GlobalChat Medien-Support",
            description="Alle unterstützten Medientypen und Limits im Überblick",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Bilder
        embed.add_field(
            name="🖼️ Bilder",
            value=(
                f"**Formate:** {', '.join(self.config.ALLOWED_IMAGE_FORMATS).upper()}\n"
                "**Max. Größe:** 25 MB pro Datei\n"
                "**Features:** Erstes Bild als Haupt-Bild, weitere als Links"
            ),
            inline=False
        )
        
        # Videos
        embed.add_field(
            name="🎥 Videos",
            value=(
                f"**Formate:** {', '.join(self.config.ALLOWED_VIDEO_FORMATS).upper()}\n"
                "**Max. Größe:** 25 MB pro Datei\n"
                "**Features:** Direkter Download-Link mit Dateiname und Größe"
            ),
            inline=False
        )
        
        # Audio
        embed.add_field(
            name="🎵 Audio",
            value=(
                f"**Formate:** {', '.join(self.config.ALLOWED_AUDIO_FORMATS).upper()}\n"
                "**Max. Größe:** 25 MB pro Datei\n"
                "**Features:** Direkter Download-Link mit Dateiname"
            ),
            inline=False
        )
        
        # Dokumente
        embed.add_field(
            name="📄 Dokumente",
            value=(
                "**Formate:** PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, ZIP, RAR, 7Z\n"
                "**Max. Größe:** 25 MB pro Datei\n"
                "**Features:** Direkter Download-Link mit Icon, Name und Größe"
            ),
            inline=False
        )
        
        # Weitere Features
        embed.add_field(
            name="✨ Weitere Features",
            value=(
                "• 🎨 **Discord Sticker** - Automatisch als Thumbnail oder Field\n"
                "• 🔗 **Link-Previews** - YouTube, Twitter, Spotify, etc. (automatisch)\n"
                "• ↩️ **Reply-Support** - Zitiere vorherige Nachrichten mit Kontext\n"
                f"• 📎 **Multi-Attachments** - Bis zu {self.config.MAX_ATTACHMENTS} Anhänge gleichzeitig\n"
                "• 🖼️ **Automatische Kategorisierung** - Intelligente Anzeige je nach Medientyp"
            ),
            inline=False
        )
        
        # Limits
        embed.add_field(
            name="⚠️ Wichtige Limits",
            value=(
                f"• **Max. {self.config.MAX_ATTACHMENTS} Anhänge** pro Nachricht\n"
                f"• **Max. {self.config.MAX_FILE_SIZE_MB} MB** pro Datei (Discord-Limit)\n"
                "• **Rate-Limit:** 5 Nachrichten pro Minute\n"
                "• **Max. 1900 Zeichen** Text (konfigurierbar)\n"
                "• Nur freigegebene Dateiformate erlaubt"
            ),
            inline=False
        )
        
        # Beispiele
        embed.add_field(
            name="💡 Beispiele",
            value=(
                "**Sende:**\n"
                "• Text + 3 Bilder → Erstes groß, Rest als Links\n"
                "• Video-Datei → Download-Link mit Größe\n"
                "• PDF-Dokument → Download mit Icon\n"
                "• YouTube-Link → Automatischer Preview\n"
                "• Reply + Sticker → Kontext + Thumbnail"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @globalchat.command(
        name="test-media",
        description="Teste den Medien-Support mit einer Demo-Nachricht"
    )
    async def test_media(self, ctx: discord.ApplicationContext):
        """Sendet eine Test-Nachricht um Medien-Support zu demonstrieren"""
        
        # Prüfen ob GlobalChat aktiv
        channel_id = db.get_globalchat_channel(ctx.guild.id)
        if not channel_id:
            await ctx.respond(
                "❌ Dieser Server nutzt GlobalChat nicht!\n"
                "Nutze `/globalchat setup` zuerst.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🧪 GlobalChat Medien-Test",
            description=(
                "Dies ist eine Test-Nachricht um den vollständigen Medien-Support zu demonstrieren.\n\n"
                "**Was wird unterstützt:**\n"
                "• Bilder, Videos und Audio-Dateien\n"
                "• Dokumente aller Art\n"
                "• Discord Sticker\n"
                "• Link-Previews von YouTube, Twitter, etc.\n"
                "• Antworten auf andere Nachrichten\n\n"
                "**So testest du:**\n"
                f"1. Gehe zu <#{channel_id}>\n"
                "2. Sende eine Nachricht mit Medien\n"
                "3. Die Nachricht erscheint auf allen Servern\n\n"
                "Probiere verschiedene Kombinationen aus!"
            ),
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 Aktuelle Limits",
            value=(
                f"• Max. {self.config.MAX_ATTACHMENTS} Anhänge\n"
                f"• Max. {self.config.MAX_FILE_SIZE_MB} MB pro Datei\n"
                "• 5 Nachrichten/Minute"
            ),
            inline=True
        )
        
        embed.add_field(
            name="✅ Unterstützte Formate",
            value=(
                "Bilder, Videos, Audio,\n"
                "Dokumente, Archive,\n"
                "Office-Dateien, PDFs"
            ),
            inline=True
        )
        
        embed.set_footer(text=f"Test von {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.respond(embed=embed, ephemeral=True)

    
def setup(bot):
    """Setup-Funktion für the cog when loaded by classic loader."""
    try:
        cog = GlobalChat(bot)
        bot.add_cog(cog)
    except Exception:
        # Keep this minimal — main setup above handles logging and DB checks.
        raise