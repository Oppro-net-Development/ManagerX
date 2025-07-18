import ezcord
import discord
from discord.ext import commands
from discord import slash_command, Option
from FastCoding import set_globalchat_channel, get_all_channels, create_tables
from FastCoding.backend.database.globalchat_db import remove_globalchat_channel, get_globalchat_channel
import asyncio
import logging
from typing import Optional, List
import re
from FastCoding import emoji_loading

# Logger konfigurieren
logger = logging.getLogger(__name__)


class GlobalChat(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        create_tables()

        # Rate limiting für Spam-Schutz
        self.message_cooldown = commands.CooldownMapping.from_cooldown(
            5, 60, commands.BucketType.user  # 5 Nachrichten pro Minute pro User
        )

        # Cache für Channel-IDs (alle 5 Minuten aktualisiert)
        self._channel_cache: List[int] = []
        self._cache_last_update = 0
        self.cache_duration = 300  # 5 Minuten

    async def _get_cached_channels(self) -> List[int]:
        """Holt Channel-IDs aus Cache oder DB"""
        import time
        current_time = time.time()

        if current_time - self._cache_last_update > self.cache_duration:
            self._channel_cache = get_all_channels()
            self._cache_last_update = current_time
            logger.debug(f"Channel cache aktualisiert: {len(self._channel_cache)} Channels")

        return self._channel_cache

    def _is_valid_message(self, message: discord.Message) -> bool:
        """Prüft ob die Nachricht valid für GlobalChat ist"""
        if message.author.bot:
            return False

        # Leere Nachrichten ignorieren
        if not message.content and not message.attachments:
            return False

        # Sehr kurze Nachrichten ignorieren (Spam-Schutz)
        if len(message.content.strip()) < 2:
            return False

        # Nachrichten nur mit Mentions ignorieren
        if message.content and message.content.strip().startswith('<@') and len(message.content.strip()) < 25:
            return False

        return True

    def _clean_message_content(self, content: str) -> str:
        """Bereinigt Nachrichteninhalt von Discord-spezifischen Elementen"""
        if not content:
            return ""

        # Entferne @everyone und @here
        content = content.replace('@everyone', '＠everyone').replace('@here', '＠here')

        # Begrenzte Länge
        if len(content) > 1900:
            content = content[:1900] + "..."

        return content

    async def _create_message_embed(self, message: discord.Message) -> discord.Embed:
        """Erstellt ein Embed für die GlobalChat-Nachricht"""
        content = self._clean_message_content(message.content)
        author_name = message.author.display_name
        embed = discord.Embed(
            title=f"» {author_name}",
            description=f"{content or '*Anhang oder Medien*'}\n\n {emoji_loading} × [Bot Einladen](https://discord.com/oauth2/authorize?client_id=1368201272624287754&permissions=8&integration_type=0&scope=bot)",
            color=discord.Color.from_rgb(88, 166, 255),
            timestamp=message.created_at
        )

        # --- Rollen ermitteln ---
        roles = []
        bot_owner_ids = [1093555256689959005]  # Ersetze mit deiner Bot-Owner-ID

        if message.author.id in bot_owner_ids:
            roles.append("Bot Owner")
        elif hasattr(self.bot, "owner_ids") and message.author.id in self.bot.owner_ids:
            roles.append("Developer")

        # Autor-Feld mit Rollen
        if roles:
            role_str = " | ".join(roles)

        embed.set_author(
            name=role_str,
            icon_url=message.author.display_avatar.url
        )

        # Anhänge anzeigen
        if message.attachments:
            image_set = False
            attachment_lines = []
            for attachment in message.attachments:
                # Prüfen ob es ein Bild ist
                if attachment.content_type and attachment.content_type.startswith("image/") and not image_set:
                    embed.set_image(url=attachment.url)  # Nur das erste Bild wird als Bild eingebunden
                    image_set = True
                else:
                    # Andere Anhänge oder weitere Bilder als Link im Feld anzeigen
                    attachment_lines.append(f"📎 [{attachment.filename}]({attachment.url})")

            if attachment_lines:
                embed.add_field(name="Anhänge", value="\n".join(attachment_lines), inline=False)

        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Hauptlogik für GlobalChat-Nachrichten"""
        # Basis-Validierung
        if not self._is_valid_message(message):
            return

        # Rate limiting prüfen
        bucket = self.message_cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            try:
                await message.add_reaction("⏰")
            except discord.Forbidden:
                pass
            return

        # Channel-IDs aus Cache holen
        channel_ids = await self._get_cached_channels()

        # Prüfen, ob Nachricht in einem GlobalChat-Channel geschrieben wurde
        if message.channel.id not in channel_ids:
            return

        try:
            # Originalnachricht löschen
            await message.delete()
        except discord.Forbidden:
            logger.warning(f"Keine Berechtigung zum Löschen in Channel {message.channel.id}")
        except discord.NotFound:
            pass  # Nachricht bereits gelöscht

        # Embed erstellen
        try:
            embed = await self._create_message_embed(message)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Embeds: {e}")
            return

        # Nachricht an alle anderen GlobalChat-Channels senden
        successful_sends = 0
        failed_sends = 0

        # Verwende asyncio.gather für parallele Verarbeitung
        tasks = []
        for channel_id in channel_ids:
            target = self.bot.get_channel(channel_id)
            if target:
                tasks.append(self._send_to_channel(target, embed))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    failed_sends += 1
                    logger.error(f"Fehler beim Senden: {result}")
                else:
                    successful_sends += 1

        logger.info(f"GlobalChat: {successful_sends} erfolgreich, {failed_sends} fehlgeschlagen")

    async def _send_to_channel(self, channel: discord.TextChannel, embed: discord.Embed) -> bool:
        """Hilfsfunktion zum Senden an einen Channel"""
        try:
            await channel.send(embed=embed)
            return True
        except discord.Forbidden:
            logger.warning(f"Keine Berechtigung zum Senden in Channel {channel.id}")
            return False
        except discord.HTTPException as e:
            logger.error(f"HTTP-Fehler beim Senden an {channel.id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Senden an {channel.id}: {e}")
            return False

    @slash_command(name="setglobal", description="Setzt einen Channel als GlobalChat")
    @commands.has_permissions(manage_channels=True)
    async def setglobal(
            self,
            ctx: discord.ApplicationContext,
            channel: Option(discord.TextChannel, "Wähle einen Channel", required=True)
    ):
        """Setzt einen Channel als GlobalChat-Channel"""
        # Prüfen ob Bot Berechtigung in dem Channel hat
        permissions = channel.permissions_for(ctx.guild.me)
        if not (permissions.send_messages and permissions.manage_messages):
            await ctx.respond(
                "❌ Der Bot benötigt die Berechtigung 'Nachrichten senden' und 'Nachrichten verwalten' in diesem Channel.",
                ephemeral=True
            )
            return

        # Prüfen ob bereits ein GlobalChat-Channel gesetzt ist
        existing_channel_id = get_globalchat_channel(ctx.guild.id)
        if existing_channel_id:
            existing_channel = ctx.guild.get_channel(existing_channel_id)
            if existing_channel:
                await ctx.respond(
                    f"⚠️ Bereits ein GlobalChat-Channel gesetzt: {existing_channel.mention}\n"
                    f"Verwende `/unsetglobal` um ihn zu entfernen.",
                    ephemeral=True
                )
                return

        # Channel setzen
        try:
            set_globalchat_channel(ctx.guild.id, channel.id)
            # Cache invalidieren
            self._cache_last_update = 0

            await ctx.respond(
                f"✅ GlobalChat-Channel wurde gesetzt: {channel.mention}\n"
                f"ℹ️ Nachrichten in diesem Channel werden automatisch an alle anderen GlobalChat-Channels weitergeleitet.",
                ephemeral=True
            )

            # Informations-Embed in den Channel senden
            info_embed = discord.Embed(
                title="🌍 GlobalChat aktiviert",
                description="Dieser Channel ist jetzt mit anderen Servern verbunden!\n"
                            "Nachrichten hier werden automatisch weitergeleitet.",
                color=discord.Color.green()
            )
            info_embed.add_field(
                name="Regeln",
                value="• Sei respektvoll\n• Kein Spam\n• Folge den Discord-Richtlinien",
                inline=False
            )
            await channel.send(embed=info_embed)

        except Exception as e:
            logger.error(f"Fehler beim Setzen des GlobalChat-Channels: {e}")
            await ctx.respond("❌ Fehler beim Setzen des GlobalChat-Channels.", ephemeral=True)

    @slash_command(name="unsetglobal", description="Entfernt den GlobalChat aus diesem Server")
    @commands.has_permissions(manage_channels=True)
    async def unsetglobal(self, ctx: discord.ApplicationContext):
        """Entfernt den GlobalChat-Channel von diesem Server"""
        try:
            removed = remove_globalchat_channel(ctx.guild.id)
            if removed:
                # Cache invalidieren
                self._cache_last_update = 0
                await ctx.respond("✅ GlobalChat-Channel wurde entfernt.", ephemeral=True)
            else:
                await ctx.respond("ℹ️ Kein GlobalChat-Channel für diesen Server gesetzt.", ephemeral=True)
        except Exception as e:
            logger.error(f"Fehler beim Entfernen des GlobalChat-Channels: {e}")
            await ctx.respond("❌ Fehler beim Entfernen des GlobalChat-Channels.", ephemeral=True)

    @slash_command(name="globalstatus", description="Zeigt GlobalChat-Status und Statistiken")
    @commands.has_permissions(manage_channels=True)
    async def globalstatus(self, ctx: discord.ApplicationContext):
        """Zeigt den Status des GlobalChats"""
        try:
            current_channel_id = get_globalchat_channel(ctx.guild.id)
            all_channels = await self._get_cached_channels()

            embed = discord.Embed(
                title="🌍 GlobalChat Status",
                color=discord.Color.blue()
            )

            if current_channel_id:
                channel = ctx.guild.get_channel(current_channel_id)
                channel_name = channel.mention if channel else f"<#{current_channel_id}>"
                embed.add_field(
                    name="Aktueller Channel",
                    value=channel_name,
                    inline=False
                )
            else:
                embed.add_field(
                    name="Aktueller Channel",
                    value="❌ Kein GlobalChat-Channel gesetzt",
                    inline=False
                )

            embed.add_field(
                name="Verbundene Server",
                value=f"{len(all_channels)} Server insgesamt",
                inline=True
            )

            embed.add_field(
                name="Cache-Status",
                value=f"Letzte Aktualisierung: <t:{int(self._cache_last_update)}:R>",
                inline=True
            )

            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Abrufen des GlobalChat-Status: {e}")
            await ctx.respond("❌ Fehler beim Abrufen des Status.", ephemeral=True)

    @setglobal.error
    @unsetglobal.error
    @globalstatus.error
    async def globalchat_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        """Fehlerbehandlung für GlobalChat-Befehle"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond(
                "❌ Du benötigst die Berechtigung 'Kanäle verwalten' um diesen Befehl zu verwenden.",
                ephemeral=True
            )
        else:
            logger.error(f"Unerwarteter Fehler in GlobalChat: {error}")
            await ctx.respond("❌ Ein unerwarteter Fehler ist aufgetreten.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(GlobalChat(bot))