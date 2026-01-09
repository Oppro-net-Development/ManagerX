"""
Welcome System Cog
==================

Umfassendes Welcome System mit Embed-Support, Auto-Roles,
DM-Nachrichten und Statistiken.
"""

import discord
from discord.ext import commands
from DevTools import WelcomeDatabase
import asyncio
import json
import io
import logging
from typing import Optional, Dict, Any
import aiosqlite
from datetime import datetime
import ezcord
from discord.ui import Container


# Logger Setup
logger = logging.getLogger(__name__)


class WelcomeSystem(ezcord.Cog):
    """
    Welcome System für Discord Server.
    
    Bietet umfassende Willkommensnachrichten mit Embed-Support,
    automatischen Rollen, privaten Nachrichten und Statistiken.
    
    Parameters
    ----------
    bot : ezcord.Bot
        Die Bot-Instanz
    
    Attributes
    ----------
    bot : ezcord.Bot
        Die Bot-Instanz
    db : WelcomeDatabase
        Datenbank-Handler für Welcome-Einstellungen
    _settings_cache : dict
        Cache für Server-Einstellungen
    _cache_timeout : int
        Cache-Timeout in Sekunden (Standard: 300)
    _rate_limit_cache : dict
        Rate-Limiting Cache für Welcome-Messages
    """
    
    def __init__(self, bot):
        """
        Initialisiert das Welcome System.
        
        Parameters
        ----------
        bot : ezcord.Bot
            Die Bot-Instanz
        """
        self.bot = bot
        self.db = WelcomeDatabase()
        # Cache für bessere Performance
        self._settings_cache = {}
        self._cache_timeout = 300  # 5 Minuten Cache
        self._rate_limit_cache = {}  # Rate Limiting
    
    async def get_cached_settings(self, guild_id: int):
        """
        Holt Einstellungen mit Cache-Unterstützung.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Returns
        -------
        dict or None
            Server-Einstellungen aus Cache oder Datenbank
        
        Notes
        -----
        Cache wird nach 5 Minuten automatisch invalidiert.
        """
        now = asyncio.get_event_loop().time()
        
        if guild_id in self._settings_cache:
            cached_data, timestamp = self._settings_cache[guild_id]
            if now - timestamp < self._cache_timeout:
                return cached_data
        
        # Aus Datenbank laden
        settings = await self.db.get_welcome_settings(guild_id)
        if settings:
            self._settings_cache[guild_id] = (settings, now)
        return settings

    def invalidate_cache(self, guild_id: int):
        """
        Invalidiert Cache für einen Server.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Notes
        -----
        Sollte nach jeder Einstellungsänderung aufgerufen werden.
        """
        if guild_id in self._settings_cache:
            del self._settings_cache[guild_id]
    
    def check_rate_limit(self, guild_id: int) -> bool:
        """
        Prüft Rate Limit für Server.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Returns
        -------
        bool
            True wenn Rate Limit nicht erreicht, False sonst
        
        Notes
        -----
        Erlaubt maximal eine Welcome Message alle 5 Sekunden pro Server.
        """
        now = asyncio.get_event_loop().time()
        if guild_id not in self._rate_limit_cache:
            self._rate_limit_cache[guild_id] = now
            return True
        
        last_time = self._rate_limit_cache[guild_id]
        if now - last_time >= 5:  # 5 Sekunden zwischen Welcome Messages
            self._rate_limit_cache[guild_id] = now
            return True
        
        return False
    
    def replace_placeholders(self, text: str, member: discord.Member, guild: discord.Guild) -> str:
        """
        Erweiterte Placeholder-Ersetzung mit Rückwärtskompatibilität.
        
        Parameters
        ----------
        text : str
            Text mit Placeholders
        member : discord.Member
            Discord Member Objekt
        guild : discord.Guild
            Discord Guild Objekt
        
        Returns
        -------
        str
            Text mit ersetzten Placeholders
        
        Notes
        -----
        Unterstützte Placeholder-Kategorien:
        - User: %user%, %username%, %mention%, %tag%, %userid%
        - Server: %servername%, %server%, %guild%, %serverid%, %membercount%
        - Zeit: %joindate%, %jointime%, %createddate%, %createdtime%, %accountage%
        - Erweitert: %roles%, %rolecount%, %highestrole%, %avatar%
        - Statistiken: %onlinemembers%, %textchannels%, %voicechannels%
        
        Examples
        --------
        >>> text = "Willkommen %mention% auf %servername%!"
        >>> replace_placeholders(text, member, guild)
        "Willkommen @User auf Mein Server!"
        """
        if not text:
            return text
        
        try:
            # Basis Placeholder (alte Version)
            placeholders = {
                '%user%': member.display_name,
                '%username%': member.name,
                '%mention%': member.mention,
                '%tag%': str(member),
                '%userid%': str(member.id),
                '%servername%': guild.name,
                '%serverid%': str(guild.id),
                '%membercount%': str(guild.member_count),
                '%joindate%': member.joined_at.strftime('%d.%m.%Y') if member.joined_at else 'Unbekannt',
                '%createddate%': member.created_at.strftime('%d.%m.%Y'),
                '%server%': guild.name,
                '%guild%': guild.name,
            }
            
            # Erweiterte Placeholder (neue Version)
            try:
                # Rolleninformationen
                roles = [role.name for role in member.roles if role.name != "@everyone"]
                highest_role = member.top_role.name if member.top_role.name != "@everyone" else "Keine"
                
                # Zeitberechnungen
                account_age = (discord.utils.utcnow() - member.created_at).days
                
                # Online-Member zählen (kann fehlschlagen bei großen Servern)
                try:
                    online_count = sum(1 for m in guild.members if m.status != discord.Status.offline)
                except:
                    online_count = "Unbekannt"
                
                extended_placeholders = {
                    # Zeitinformationen
                    '%jointime%': member.joined_at.strftime('%H:%M') if member.joined_at else 'Unbekannt',
                    '%createdtime%': member.created_at.strftime('%H:%M'),
                    '%accountage%': f"{account_age} Tage",
                    
                    # Erweiterte Infos
                    '%discriminator%': member.discriminator if hasattr(member, 'discriminator') else "0000",
                    '%roles%': ', '.join(roles) if roles else 'Keine',
                    '%rolecount%': str(len(roles)),
                    '%highestrole%': highest_role,
                    '%avatar%': member.display_avatar.url,
                    '%defaultavatar%': member.default_avatar.url,
                    
                    # Server Statistiken
                    '%onlinemembers%': str(online_count),
                    '%textchannels%': str(len(guild.text_channels)),
                    '%voicechannels%': str(len(guild.voice_channels)),
                    '%categories%': str(len(guild.categories)),
                    '%emojis%': str(len(guild.emojis)),
                }
                
                placeholders.update(extended_placeholders)
                
            except Exception as e:
                logger.warning(f"Erweiterte Placeholder fehlgeschlagen: {e}")
        
        except Exception as e:
            logger.error(f"Placeholder Fehler: {e}")
            return text
        
        # Placeholder ersetzen
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, str(value))
        
        return text
    
    async def send_welcome_dm(self, member: discord.Member, settings: dict):
        """
        Sendet private Willkommensnachricht.
        
        Parameters
        ----------
        member : discord.Member
            Neues Mitglied
        settings : dict
            Server-Einstellungen
        
        Notes
        -----
        Fehler beim DM-Versand werden geloggt aber nicht als Fehler behandelt,
        da viele User DMs deaktiviert haben.
        """
        try:
            if not settings.get('join_dm_enabled'):
                return
                
            dm_message = settings.get('join_dm_message', 
                'Willkommen auf **%servername%**! Schön, dass du da bist! 🎉')
            
            processed_message = self.replace_placeholders(dm_message, member, member.guild)
            
            await member.send(processed_message)
            logger.info(f"Welcome DM an {member} gesendet")
            
        except discord.Forbidden:
            logger.warning(f"Konnte keine DM an {member} senden - DMs deaktiviert")
        except Exception as e:
            logger.error(f"Fehler beim Senden der Welcome DM: {e}")
    
    async def assign_auto_role(self, member: discord.Member, settings: dict):
        """
        Vergibt automatische Rolle.
        
        Parameters
        ----------
        member : discord.Member
            Neues Mitglied
        settings : dict
            Server-Einstellungen mit auto_role_id
        
        Notes
        -----
        Prüft automatisch Berechtigungen und Rollen-Hierarchie.
        """
        try:
            auto_role_id = settings.get('auto_role_id')
            if not auto_role_id:
                return
            
            role = member.guild.get_role(auto_role_id)
            if not role:
                logger.warning(f"Auto-Role {auto_role_id} nicht gefunden in {member.guild.name}")
                return
            
            if role >= member.guild.me.top_role:
                logger.warning(f"Auto-Role {role.name} ist höher als Bot-Rolle")
                return
            
            await member.add_roles(role, reason="Welcome Auto-Role")
            logger.info(f"Auto-Role {role.name} an {member} vergeben")
            
        except discord.Forbidden:
            logger.error(f"Keine Berechtigung für Auto-Role")
        except Exception as e:
            logger.error(f"Auto-Role Fehler: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Event wird ausgelöst, wenn ein neuer User dem Server beitritt.
        
        Parameters
        ----------
        member : discord.Member
            Neues Mitglied
        
        Notes
        -----
        Führt folgende Aktionen aus (wenn aktiviert):
        1. Rate Limiting Check
        2. Einstellungen aus Cache/DB laden
        3. Auto-Role vergeben
        4. Welcome Message senden (Channel)
        5. Welcome DM senden
        6. Statistiken aktualisieren
        """
        try:
            # Rate Limiting prüfen
            if not self.check_rate_limit(member.guild.id):
                logger.info(f"Rate Limit aktiv für {member.guild.name}")
                return
            
            settings = await self.get_cached_settings(member.guild.id)
            
            if not settings or not settings.get('enabled', True):
                return
            
            # Channel validieren
            channel_id = settings.get('channel_id')
            if not channel_id:
                logger.warning(f"Kein Welcome Channel für {member.guild.name} gesetzt")
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Welcome Channel {channel_id} nicht gefunden")
                # Channel aus DB entfernen
                await self.db.update_welcome_settings(member.guild.id, channel_id=None)
                self.invalidate_cache(member.guild.id)
                return
            
            # Permissions prüfen
            perms = channel.permissions_for(member.guild.me)
            if not perms.send_messages:
                logger.error(f"Keine Send-Berechtigung in {channel.name}")
                return
            
            # Auto-Role vergeben
            await self.assign_auto_role(member, settings)
            
            # Welcome Message
            welcome_message = settings.get('welcome_message', 'Willkommen %mention% auf **%servername%**! 🎉')
            processed_message = self.replace_placeholders(welcome_message, member, member.guild)
            
            # Embed oder normale Nachricht
            if settings.get('embed_enabled', False) and perms.embed_links:
                await self.send_embed_welcome(channel, member, settings, processed_message)
            else:
                msg = await channel.send(processed_message)
                await self.handle_auto_delete(msg, settings)
            
            # Private Nachricht senden
            await self.send_welcome_dm(member, settings)
            
            # Statistiken aktualisieren
            if settings.get('welcome_stats_enabled'):
                await self.db.update_welcome_stats(member.guild.id, joins=1)
                
        except Exception as e:
            logger.exception(f"Welcome System Fehler für {member}: {e}")
    
    async def send_embed_welcome(self, channel, member, settings, processed_message):
        """
        Sendet Embed Welcome Message.
        
        Parameters
        ----------
        channel : discord.TextChannel
            Ziel-Channel
        member : discord.Member
            Neues Mitglied
        settings : dict
            Server-Einstellungen
        processed_message : str
            Verarbeitete Welcome Message (Fallback)
        
        Notes
        -----
        Fallback auf normale Nachricht bei Embed-Fehlern.
        """
        try:
            embed = discord.Embed()
            
            # Embed Farbe
            color_hex = settings.get('embed_color', '#00ff00')
            try:
                color = int(color_hex.replace('#', ''), 16)
                embed.color = discord.Color(color)
            except:
                embed.color = discord.Color.green()
            
            # Embed Titel
            embed_title = settings.get('embed_title')
            if embed_title:
                embed.title = self.replace_placeholders(embed_title, member, member.guild)
            
            # Embed Beschreibung
            embed_description = settings.get('embed_description')
            if embed_description:
                embed.description = self.replace_placeholders(embed_description, member, member.guild)
            else:
                embed.description = processed_message
            
            # Embed Thumbnail
            if settings.get('embed_thumbnail', False):
                embed.set_thumbnail(url=member.display_avatar.url)
            
            # Embed Footer
            embed_footer = settings.get('embed_footer')
            if embed_footer:
                embed.set_footer(text=self.replace_placeholders(embed_footer, member, member.guild))
            
            # Nachricht senden
            content = member.mention if settings.get('ping_user', False) else None
            msg = await channel.send(content=content, embed=embed)
            
            await self.handle_auto_delete(msg, settings)
            
        except Exception as e:
            logger.error(f"Embed Welcome Fehler: {e}")
            # Fallback auf normale Nachricht
            msg = await channel.send(processed_message)
            await self.handle_auto_delete(msg, settings)
    
    async def handle_auto_delete(self, message, settings):
        """
        Behandelt automatisches Löschen von Nachrichten.
        
        Parameters
        ----------
        message : discord.Message
            Zu löschende Nachricht
        settings : dict
            Server-Einstellungen mit delete_after
        
        Notes
        -----
        Wartet die angegebene Zeit und löscht dann die Nachricht.
        Fehler beim Löschen werden geloggt aber nicht weitergegeben.
        """
        try:
            delete_after = settings.get('delete_after', 0)
            if delete_after > 0:
                await asyncio.sleep(delete_after)
                try:
                    await message.delete()
                except discord.NotFound:
                    pass  # Message bereits gelöscht
                except discord.Forbidden:
                    logger.warning("Keine Berechtigung zum Löschen der Welcome Message")
        except Exception as e:
            logger.error(f"Auto-Delete Fehler: {e}")
    
    # Alle Commands bleiben gleich, aber mit Cache-Invalidierung
    welcome = discord.SlashCommandGroup("welcome", "Welcome System Einstellungen")
    
    @welcome.command(name="channel", description="Setzt den Welcome Channel")
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        """
        Setzt den Channel für Welcome Messages.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        channel : discord.TextChannel
            Ziel-Channel für Welcome Messages
        """
        success = await self.db.update_welcome_settings(ctx.guild.id, channel_id=channel.id)
        self.invalidate_cache(ctx.guild.id)
        
        if success:
            container = Container()
            container.add_text(
                f"{emoji_yes} Welcome Channel gesetzt"
            )
            container.add_separator()
            container.add_text(
                f"Welcome Messages werden nun in {channel.mention} gesendet."
            )
            view = discord.ui.View(container, timeout=None)
        else:
            container = Container()
            container.add_text(
                f"{emoji_no} Fehler"
            )
            container.add_separator()
            container.add_text(
                "Der Welcome Channel konnte nicht gesetzt werden."
            ) 
            view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)
    
    @welcome.command(name="message", description="Setzt die Welcome Message über ein Modal")
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_message(self, ctx):
        """
        Öffnet ein Modal zum Setzen der Welcome Message.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Zeigt ein Modal mit der aktuellen Message als Vorausfüllung.
        Bietet nach dem Speichern eine Vorschau der neuen Message.
        """
        
        # Aktuelle Einstellungen laden für Vorausfüllung
        current_settings = await self.get_cached_settings(ctx.guild.id)
        current_message = current_settings.get('welcome_message', '') if current_settings else ''
        
        class WelcomeMessageModal(discord.ui.Modal):
            """
            Modal für Welcome Message Konfiguration.
            
            Parameters
            ----------
            cog : WelcomeSystem
                Parent Cog Instanz
            current_msg : str, optional
                Aktuelle Message für Vorausfüllung
            """
            
            def __init__(self, cog, current_msg=""):
                super().__init__(title="Welcome Message konfigurieren")
                self.cog = cog
                
                self.message_input = discord.ui.InputText(
                    label="Welcome Message",
                    placeholder="z.B: Willkommen %mention% auf **%servername%**! 🎉",
                    style=discord.InputTextStyle.long,
                    value=current_msg,
                    max_length=2000,
                    required=True
                )
                self.add_item(self.message_input)
            
            async def callback(self, interaction: discord.Interaction):
                """
                Callback nach Modal-Submit.
                
                Parameters
                ----------
                interaction : discord.Interaction
                    Modal Interaction
                """
                message = self.message_input.value.strip()
                
                if not message:
                    embed = discord.Embed(
                        title="❌ Fehler",
                        description="Die Welcome Message darf nicht leer sein.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                success = await self.cog.db.update_welcome_settings(interaction.guild.id, welcome_message=message)
                self.cog.invalidate_cache(interaction.guild.id)
                
                if success:
                    # Vorschau erstellen
                    preview = self.cog.replace_placeholders(message, interaction.user, interaction.guild)
                    
                    container = Container()
                    container.add_text(
                        "# ✅ Welcome Message gesetzt"
                    )
                    container.add_separator()
                    container.add_text(
                        "## 💬 Neue Message\n\n"
                        f"```{message[:500]}{'...' if len(message) > 500 else ''}```"
                    )
                    container.add_separator()
                    container.add_text(
                        "## 👀 Vorschau (mit deinen Daten)\n\n"
                        f"{preview[:500] + ("..." if len(preview) > 500 else "")}\n\n"
                        "-# 💡 Tipp: Verwende `/welcome test` für eine vollständige Vorschau oder `/welcome placeholders` für alle verfügbaren Optionen."
                    )
                    view = discord.ui.View(container, timeout=None)
                else:
                    container = Container()
                    container.add_text(
                        "# ❌ Fehler\nDie Welcome Message konnte nicht gesetzt werden."
                    )
                    view = discord.ui.View(container, timeout=None)
                await interaction.response.send_message(view=view)
        
        modal = WelcomeMessageModal(self, current_message)
        await ctx.send_modal(modal)
    
    @welcome.command(name="toggle", description="Schaltet das Welcome System ein/aus")
    @commands.has_permissions(manage_guild=True)
    async def toggle_welcome(self, ctx):
        """
        Schaltet das Welcome System ein oder aus.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        """
        new_state = await self.db.toggle_welcome(ctx.guild.id)
        self.invalidate_cache(ctx.guild.id)
        
        if new_state is None:
            container = Container()
            container.add_text(
                "# ❌ Fehler\nEs sind noch keine Welcome Einstellungen vorhanden. Setze zuerst einen Channel."
            )
            view = discord.ui.View(container, timeout=None)
        else:
            status = "aktiviert" if new_state else "deaktiviert"
            container = Container()
            container.add_text(
                f"# ✅ Welcome System {status}"
            )
            container.add_separator()
            container.add_text(
                f"Das Welcome System wurde **{status}**."
            )
            view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)
    
    @welcome.command(name="embed", description="Aktiviert/Deaktiviert Embed Modus")
    @commands.has_permissions(manage_guild=True)
    async def toggle_embed(self, ctx, enabled: bool):
        """
        Aktiviert oder deaktiviert Embed Welcome Messages.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        enabled : bool
            True für Embed-Modus, False für normale Nachrichten
        """
        success = await self.db.update_welcome_settings(ctx.guild.id, embed_enabled=enabled)
        self.invalidate_cache(ctx.guild.id)
        
        if success:
            status = "aktiviert" if enabled else "deaktiviert"
            container = Container(
                f"# ✅ Embed Modus {status}"
            )
            container.add_separator()
            container.add_text(
                f"Welcome Messages werden nun {'als Embed' if enabled else 'als normale Nachricht'} gesendet."
            )
            view = discord.ui.View(container, timeout=None)
        else:
            container = Container()
            container.add_text(
                "# ❌ Fehler\nDer Embed Modus konnte nicht geändert werden."
            )
            view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)
    
    @welcome.command(name="autorole", description="Setzt eine Rolle die automatisch vergeben wird")
    @commands.has_permissions(manage_roles=True)
    async def set_auto_role(self, ctx, role: discord.Role = None):
        """
        Setzt eine Rolle die bei Join automatisch vergeben wird.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        role : discord.Role, optional
            Rolle zum automatischen Vergeben (None zum Entfernen)
        
        Notes
        -----
        Prüft automatisch die Rollen-Hierarchie.
        """
        if role is None:
            # Auto-Role entfernen
            success = await self.db.update_welcome_settings(ctx.guild.id, auto_role_id=None)
            self.invalidate_cache(ctx.guild.id)
            
            container = Container()
            container.add_text(
                "# ✅ Auto-Role entfernt"
            )
            container.add_separator()
            container.add_text(
                "Neue Mitglieder erhalten keine automatische Rolle mehr."
            )
            view = discord.ui.View(container, timeout=None)

        else:
            # Rolle validieren
            if role >= ctx.guild.me.top_role:
                container = Container()
                container.add_text(
                    "# ❌ Fehler\nDiese Rolle ist höher als meine höchste Rolle. Ich kann sie nicht vergeben."
                )
                view = discord.ui.View(container, timeout=None)
                await ctx.respond(view=view)
                return
            
            success = await self.db.update_welcome_settings(ctx.guild.id, auto_role_id=role.id)
            self.invalidate_cache(ctx.guild.id)
            
            if success:
                container = Container()
                container.add_text(
                    "# ✅ Auto-Role gesetzt"
                )
                container.add_separator()
                container.add_text(
                    f"Neue Mitglieder erhalten automatisch die Rolle {role.mention}."
                )
                view = discord.ui.View(container, timeout=None)
            else:
                container = Container()
                container.add_text(
                    "# ❌ Fehler\nDie Auto-Role konnte nicht gesetzt werden."
                )
                view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)
    
    @welcome.command(name="dm", description="Aktiviert/Konfiguriert private Willkommensnachrichten")
    @commands.has_permissions(manage_guild=True)
    async def setup_join_dm(self, ctx, enabled: bool, *, message: str = None):
        """
        Konfiguriert private Willkommensnachrichten.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        enabled : bool
            True zum Aktivieren, False zum Deaktivieren
        message : str, optional
            Custom DM Message (verwendet Standard wenn nicht angegeben)
        """
        settings = {'join_dm_enabled': enabled}
        if message and enabled:
            settings['join_dm_message'] = message
        
        success = await self.db.update_welcome_settings(ctx.guild.id, **settings)
        self.invalidate_cache(ctx.guild.id)
        
        if success:
            if enabled:
                if message:
                    description = f"Private Welcome Messages aktiviert!\n**Nachricht:** {message[:500]}{'...' if len(message) > 500 else ''}"
                else:
                    description = "Private Welcome Messages aktiviert! (Standard-Nachricht wird verwendet)"
            else:
                description = "Private Welcome Messages deaktiviert."
            
            container = Container()
            container.add_text(
                "# ✅ DM Einstellungen aktualisiert"
            )
            container.add_separator()
            container.add_text(
                f"{description}"
            )
            view = discord.ui.View(container, timeout=None)
        else:
            container = Container()
            container.add_text(
                "# ❌ Fehler\nDie DM Einstellungen konnten nicht aktualisiert werden."
            )
            view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)
    
    @welcome.command(name="template", description="Lädt eine Vorlage")
    @commands.has_permissions(manage_guild=True)
    async def load_template(self, ctx, template_name: str):
        """
        Lädt eine vordefinierte Vorlage.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        template_name : str
            Name der Vorlage (basic, fancy, minimal, detailed)
        
        Notes
        -----
        Verfügbare Vorlagen:
        - basic: Einfache Text-Nachricht
        - fancy: Embed mit Thumbnail und Farbe
        - minimal: Minimalistischer Text
        - detailed: Detailliertes Embed mit vielen Infos
        """
        templates = {
            "basic": {
                "welcome_message": "Willkommen %mention% auf **%servername%**! 🎉",
                "embed_enabled": False,
                "template_name": "basic"
            },
            "fancy": {
                "welcome_message": None,
                "embed_enabled": True,
                "embed_title": "Willkommen auf %servername%! 🎉",
                "embed_description": "Hey %user%! Du bist unser **%membercount%.** Mitglied!\n\nViel Spaß auf unserem Server! 🚀",
                "embed_color": "#ff6b6b",
                "embed_thumbnail": True,
                "embed_footer": "Beigetreten am %joindate%",
                "template_name": "fancy"
            },
            "minimal": {
                "welcome_message": "%user% ist dem Server beigetreten.",
                "embed_enabled": False,
                "template_name": "minimal"
            },
            "detailed": {
                "welcome_message": None,
                "embed_enabled": True,
                "embed_title": "🎊 Neues Mitglied!",
                "embed_description": "**%mention%** ist **%servername%** beigetreten!\n\n👤 **Username:** %username%\n📅 **Account erstellt:** %createddate%\n📊 **Mitglied Nr.:** %membercount%\n⏰ **Beigetreten um:** %jointime%",
                "embed_color": "#00d4ff",
                "embed_thumbnail": True,
                "embed_footer": "%servername% • %membercount% Mitglieder",
                "template_name": "detailed"
            }
        }
        
        if template_name not in templates:
            available = ", ".join(templates.keys())
            embed = discord.Embed(
                title="❌ Unbekannte Vorlage",
                description=f"**Verfügbare Vorlagen:** {available}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)
            return
        
        template = templates[template_name]
        success = await self.db.update_welcome_settings(ctx.guild.id, **template)
        self.invalidate_cache(ctx.guild.id)
        
        if success:
            embed = discord.Embed(
                title=f"✅ Vorlage '{template_name}' geladen",
                description="Die Welcome-Konfiguration wurde aktualisiert.",
                color=discord.Color.green()
            )
            
            # Vorschau anzeigen
            if template_name == "basic":
                embed.add_field(name="Vorschau", value="Willkommen @User auf **Servername**! 🎉", inline=False)
            elif template_name == "minimal":
                embed.add_field(name="Vorschau", value="Username ist dem Server beigetreten.", inline=False)
            else:
                embed.add_field(name="Typ", value="Embed-Nachricht", inline=False)
        else:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Die Vorlage konnte nicht geladen werden.",
                color=discord.Color.red()
            )
        
        await ctx.respond(embed=embed)
    
    @welcome.command(name="config", description="Zeigt die aktuelle Konfiguration")
    @commands.has_permissions(manage_messages=True)
    async def show_config(self, ctx):
        """
        Zeigt die aktuelle Welcome Konfiguration.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Zeigt alle konfigurierten Einstellungen übersichtlich an.
        """
        settings = await self.get_cached_settings(ctx.guild.id)
        
        if not settings:
            container = Container()
            container.add_text(
                "# ❌ Keine Konfiguration gefunden\nEs sind noch keine Welcome Einstellungen vorhanden."
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)
            return
        
        channel = self.bot.get_channel(settings.get('channel_id')) if settings.get('channel_id') else None
        auto_role = ctx.guild.get_role(settings.get('auto_role_id')) if settings.get('auto_role_id') else None
        container = Container()
        container.add_text(
            "# ⚙️ Welcome System Konfiguration"
        )
        container.add_separator()
        container.add_text(
            "## 📊 Status\n"
            f"{'✅ Aktiviert' if settings.get('enabled') else '❌ Deaktiviert'}"
        )

        container.add_text(
            "## 📢 Channel\n"
            f"{channel.mention if channel else '❌ Nicht gesetzt'}"
        )

        container.add_text(
            "## 🎨 Embed Modus\n"
            f"{'✅ Aktiviert' if settings.get('embed_enabled') else '❌ Deaktiviert'}"
        )

        container.add_text(
            "## 🏷️ Auto-Role\n"
            f"{auto_role.mention if auto_role else '❌ Rolle nicht gefunden'}"
        )

        if settings.get('join_dm_enabled'):
            container.add_text(
                "## 💌 Private Nachricht\n✅ Aktiviert"
            )

        if settings.get('template_name'):
            container.add_text(
                "## 📋 Vorlage\n"
                f"{settings.get('template_name').title()}"
            )

        message = settings.get('welcome_message', 'Nicht gesetzt')
        if len(message) > 100:
            message = message[:100] + "..."
        container.add_text(
            "## 💬 Welcome Message\n"
            f"{message}"
        )

        if settings.get('delete_after', 0) > 0:
            container.add_text(
                "## 🗑️ Auto-Delete\n"
                f"{settings.get('delete_after')} Sekunden"
            )
        view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)
    
    @welcome.command(name="test", description="Testet die Welcome Message")
    @commands.has_permissions(manage_messages=True)
    async def test_welcome(self, ctx):
        """
        Testet die Welcome Message mit dem aktuellen User.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Simuliert einen Member Join mit den aktuellen Einstellungen.
        Zeigt eine Vorschau ohne tatsächlich eine Welcome Message zu senden.
        """
        settings = await self.get_cached_settings(ctx.guild.id)
        
        if not settings:
            container = Container()
            container.add_text(
                "# ❌ Fehler\nEs sind noch keine Welcome Einstellungen vorhanden."
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
            return
        
        if not settings.get('channel_id'):
            container = Container()
            container.add_text(
                "# ❌ Fehler\nEs ist kein Welcome Channel gesetzt."
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
            return
        
        # Simuliere Member Join Event
        member = ctx.author
        welcome_message = settings.get('welcome_message', 'Willkommen %mention% auf **%servername%**! 🎉')
        processed_message = self.replace_placeholders(welcome_message, member, ctx.guild)
        
        embed = discord.Embed(
            title="🧪 Welcome Message Test",
            color=discord.Color.blue()
        )
        
        if settings.get('embed_enabled'):
            embed.add_field(
                name="Typ", 
                value="Embed-Nachricht", 
                inline=True
            )
            
            test_embed_title = settings.get('embed_title', 'Kein Titel')
            if test_embed_title:
                test_embed_title = self.replace_placeholders(test_embed_title, member, ctx.guild)
                embed.add_field(name="Embed Titel", value=test_embed_title, inline=False)
            
            test_embed_desc = settings.get('embed_description', processed_message)
            if test_embed_desc:
                test_embed_desc = self.replace_placeholders(test_embed_desc, member, ctx.guild)
                embed.add_field(name="Embed Beschreibung", value=test_embed_desc[:500] + ("..." if len(test_embed_desc) > 500 else ""), inline=False)
        else:
            embed.add_field(
                name="Typ", 
                value="Normale Nachricht", 
                inline=True
            )
            embed.add_field(
                name="Vorschau", 
                value=processed_message[:500] + ("..." if len(processed_message) > 500 else ""), 
                inline=False
            )
        
        # Zusätzliche Infos
        if settings.get('auto_role_id'):
            auto_role = ctx.guild.get_role(settings.get('auto_role_id'))
            embed.add_field(
                name="🏷️ Auto-Role",
                value=auto_role.mention if auto_role else "❌ Rolle nicht gefunden",
                inline=True
            )
        
        if settings.get('join_dm_enabled'):
            embed.add_field(
                name="💌 Private Nachricht",
                value="✅ Würde gesendet werden",
                inline=True
            )
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @welcome.command(name="placeholders", description="Zeigt alle verfügbaren Placeholder")
    async def show_placeholders(self, ctx):
        """
        Zeigt alle verfügbaren Placeholder.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Liste aller unterstützten Placeholder mit Beschreibungen.
        """
        embed = discord.Embed(
            title="📝 Verfügbare Placeholder",
            description="Diese Placeholder können in Welcome Messages verwendet werden:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👤 User Informationen",
            value=(
                "`%user%` - Username (Display Name)\n"
                "`%username%` - Echter Username\n"
                "`%mention%` - User erwähnen (@User)\n"
                "`%tag%` - User#1234\n"
                "`%userid%` - User ID\n"
                "`%discriminator%` - User Discriminator"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🏠 Server Informationen",
            value=(
                "`%servername%` - Servername\n"
                "`%server%` - Servername (Alternative)\n"
                "`%guild%` - Servername (Alternative)\n"
                "`%serverid%` - Server ID\n"
                "`%membercount%` - Mitgliederanzahl\n"
                "`%onlinemembers%` - Online Mitglieder"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏰ Zeit & Datum",
            value=(
                "`%joindate%` - Beitrittsdatum (DD.MM.YYYY)\n"
                "`%jointime%` - Beitrittszeit (HH:MM)\n"
                "`%createddate%` - Account Erstellung (DD.MM.YYYY)\n"
                "`%createdtime%` - Account Erstellung (HH:MM)\n"
                "`%accountage%` - Account Alter in Tagen"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎭 Erweiterte Informationen",
            value=(
                "`%roles%` - Alle Rollen (außer @everyone)\n"
                "`%rolecount%` - Anzahl der Rollen\n"
                "`%highestrole%` - Höchste Rolle\n"
                "`%avatar%` - Avatar URL\n"
                "`%defaultavatar%` - Standard Avatar URL"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Server Statistiken",
            value=(
                "`%textchannels%` - Anzahl Textchannels\n"
                "`%voicechannels%` - Anzahl Voicechannels\n"
                "`%categories%` - Anzahl Kategorien\n"
                "`%emojis%` - Anzahl Emojis"
            ),
            inline=False
        )
        
        embed.set_footer(text="Beispiel: Willkommen %mention%! Du bist Mitglied #%membercount% auf %servername%")
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @welcome.command(name="export", description="Exportiert die Welcome Konfiguration")
    @commands.has_permissions(administrator=True)
    async def export_config(self, ctx):
        """
        Exportiert die aktuelle Konfiguration als JSON-Datei.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Erstellt eine JSON-Datei mit allen Einstellungen.
        Sensible Daten (IDs, Timestamps) werden entfernt.
        """
        settings = await self.get_cached_settings(ctx.guild.id)
        if not settings:
            embed = discord.Embed(
                title="❌ Keine Konfiguration zum Exportieren",
                description="Es sind noch keine Welcome Einstellungen vorhanden.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        try:
            # Sensible Daten entfernen
            export_data = {k: v for k, v in settings.items() 
                          if k not in ['guild_id', 'created_at', 'updated_at']}
            
            # JSON Export erstellen
            config_json = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Als Datei senden
            file_content = f"# Welcome System Export für {ctx.guild.name}\n# Exportiert am {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n{config_json}"
            file = discord.File(
                io.StringIO(file_content), 
                filename=f"welcome_config_{ctx.guild.name.replace(' ', '_')}.json"
            )
            
            embed = discord.Embed(
                title="📄 Konfiguration exportiert",
                description="Die aktuelle Welcome-Konfiguration wurde als Datei exportiert.",
                color=discord.Color.green()
            )
            
            await ctx.respond(embed=embed, file=file, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Export Fehler: {e}")
            embed = discord.Embed(
                title="❌ Export fehlgeschlagen",
                description="Es ist ein Fehler beim Exportieren aufgetreten.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
    
    @welcome.command(name="stats", description="Zeigt Welcome Statistiken")
    @commands.has_permissions(manage_messages=True)
    async def show_stats(self, ctx):
        """
        Zeigt Welcome Statistiken für den Server.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Zeigt Statistiken für:
        - Heute
        - Diese Woche (letzte 7 Tage)
        - Gesamt (seit Aktivierung)
        """
        try:
            await self.db.migrate_database()
            
            # Statistiken aktivieren falls noch nicht geschehen
            settings = await self.get_cached_settings(ctx.guild.id)
            if settings and not settings.get('welcome_stats_enabled'):
                await self.db.update_welcome_settings(ctx.guild.id, welcome_stats_enabled=True)
                self.invalidate_cache(ctx.guild.id)
            
            # Aktuelle Statistiken aus der DB holen
            try:
                async with aiosqlite.connect(self.db.db_path) as conn:
                    # Heute
                    today = datetime.now().strftime('%Y-%m-%d')
                    cursor = await conn.execute(
                        'SELECT joins, leaves FROM welcome_stats WHERE guild_id = ? AND date = ?',
                        (ctx.guild.id, today)
                    )
                    today_stats = await cursor.fetchone()
                    
                    # Letzte 7 Tage
                    cursor = await conn.execute('''
                        SELECT SUM(joins) as total_joins, SUM(leaves) as total_leaves 
                        FROM welcome_stats 
                        WHERE guild_id = ? AND date >= date('now', '-7 days')
                    ''', (ctx.guild.id,))
                    week_stats = await cursor.fetchone()
                    
                    # Gesamt
                    cursor = await conn.execute('''
                        SELECT SUM(joins) as total_joins, SUM(leaves) as total_leaves 
                        FROM welcome_stats 
                        WHERE guild_id = ?
                    ''', (ctx.guild.id,))
                    total_stats = await cursor.fetchone()
                    
                embed = discord.Embed(
                    title="📊 Welcome Statistiken",
                    description=f"Statistiken für **{ctx.guild.name}**",
                    color=discord.Color.blue()
                )
                
                # Heute
                today_joins = today_stats[0] if today_stats else 0
                today_leaves = today_stats[1] if today_stats else 0
                embed.add_field(
                    name="📅 Heute",
                    value=f"👋 **Beigetreten:** {today_joins}\n🚪 **Verlassen:** {today_leaves}",
                    inline=True
                )
                
                # Diese Woche
                week_joins = week_stats[0] if week_stats and week_stats[0] else 0
                week_leaves = week_stats[1] if week_stats and week_stats[1] else 0
                embed.add_field(
                    name="📅 Diese Woche",
                    value=f"👋 **Beigetreten:** {week_joins}\n🚪 **Verlassen:** {week_leaves}",
                    inline=True
                )
                
                # Gesamt
                total_joins = total_stats[0] if total_stats and total_stats[0] else 0
                total_leaves = total_stats[1] if total_stats and total_stats[1] else 0
                embed.add_field(
                    name="📊 Gesamt",
                    value=f"👋 **Beigetreten:** {total_joins}\n🚪 **Verlassen:** {total_leaves}",
                    inline=True
                )
                
                # Aktuelle Server Info
                embed.add_field(
                    name="ℹ️ Server Info",
                    value=f"👥 **Aktuelle Mitglieder:** {ctx.guild.member_count}\n📈 **Netto Wachstum:** {total_joins - total_leaves}",
                    inline=False
                )
                
                embed.set_footer(text="Statistiken werden seit der Aktivierung des Systems gesammelt")
                
            except Exception as e:
                logger.error(f"Stats DB Error: {e}")
                embed = discord.Embed(
                    title="📊 Welcome Statistiken",
                    description="Statistiken werden ab sofort gesammelt und beim nächsten Aufruf angezeigt.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="ℹ️ Server Info",
                    value=f"👥 **Aktuelle Mitglieder:** {ctx.guild.member_count}",
                    inline=False
                )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Stats Command Error: {e}")
            embed = discord.Embed(
                title="❌ Fehler",
                description="Statistiken konnten nicht geladen werden.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
    
    @welcome.command(name="reset", description="Setzt alle Welcome Einstellungen zurück")
    @commands.has_permissions(administrator=True)
    async def reset_welcome(self, ctx):
        """
        Setzt alle Welcome Einstellungen zurück.
        
        Parameters
        ----------
        ctx : discord.ApplicationContext
            Slash Command Context
        
        Notes
        -----
        Zeigt eine Bestätigungsabfrage vor dem Löschen.
        Diese Aktion kann nicht rückgängig gemacht werden.
        """
        
        # Bestätigungs-View
        class ConfirmView(discord.ui.View):
            """
            Bestätigungs-View für Reset.
            
            Attributes
            ----------
            confirmed : bool
                Ob der Reset bestätigt wurde
            """
            
            def __init__(self):
                super().__init__(timeout=30)
                self.confirmed = False
            
            @discord.ui.button(label="✅ Ja, zurücksetzen", style=discord.ButtonStyle.danger)
            async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                """
                Bestätigung des Resets.
                
                Parameters
                ----------
                button : discord.ui.Button
                    Geklickter Button
                interaction : discord.Interaction
                    Button Interaction
                """
                self.confirmed = True
                self.stop()
                
                success = await ctx.cog.db.delete_welcome_settings(ctx.guild.id)
                ctx.cog.invalidate_cache(ctx.guild.id)
                
                if success:
                    embed = discord.Embed(
                        title="✅ Einstellungen zurückgesetzt",
                        description="Alle Welcome Einstellungen wurden erfolgreich gelöscht.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Fehler",
                        description="Die Einstellungen konnten nicht zurückgesetzt werden.",
                        color=discord.Color.red()
                    )
                
                await interaction.response.edit_message(embed=embed, view=None)
            
            @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary)
            async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                """
                Abbruch des Resets.
                
                Parameters
                ----------
                button : discord.ui.Button
                    Geklickter Button
                interaction : discord.Interaction
                    Button Interaction
                """
                self.stop()
                
                embed = discord.Embed(
                    title="❌ Abgebrochen",
                    description="Die Einstellungen wurden nicht zurückgesetzt.",
                    color=discord.Color.orange()
                )
                
                await interaction.response.edit_message(embed=embed, view=None)
        
        embed = discord.Embed(
            title="⚠️ Einstellungen zurücksetzen",
            description="Bist du sicher, dass du **alle** Welcome Einstellungen löschen möchtest?\n\n**Diese Aktion kann nicht rückgängig gemacht werden!**",
            color=discord.Color.orange()
        )
        
        view = ConfirmView()
        await ctx.respond(embed=embed, view=view, ephemeral=True)
    
    # Event Listeners für Statistiken
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Tracking für Member Leaves.
        
        Parameters
        ----------
        member : discord.Member
            Mitglied das den Server verlassen hat
        
        Notes
        -----
        Aktualisiert die Statistiken wenn aktiviert.
        """
        try:
            settings = await self.get_cached_settings(member.guild.id)
            if settings and settings.get('welcome_stats_enabled'):
                await self.db.update_welcome_stats(member.guild.id, leaves=1)
        except Exception as e:
            logger.error(f"Leave Stats Error: {e}")


def setup(bot):
    """
    Setup-Funktion für das Cog.
    
    Parameters
    ----------
    bot : ezcord.Bot
        Bot-Instanz
    
    Notes
    -----
    Wird automatisch von discord.py beim Laden des Cogs aufgerufen.
    """
    bot.add_cog(WelcomeSystem(bot))