import discord
from discord.ext import commands
from DevTools import WelcomeDatabase  # Korrigierter Import
import asyncio
import json
import io
import logging
from typing import Optional, Dict, Any
import aiosqlite
from datetime import datetime
import ezcord

# Logger Setup
logger = logging.getLogger(__name__)

class WelcomeSystem(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = WelcomeDatabase()
        # Cache für bessere Performance
        self._settings_cache = {}
        self._cache_timeout = 300  # 5 Minuten Cache
        self._rate_limit_cache = {}  # Rate Limiting
    
    async def get_cached_settings(self, guild_id: int):
        """Holt Einstellungen mit Cache"""
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
        """Invalidiert Cache für einen Server"""
        if guild_id in self._settings_cache:
            del self._settings_cache[guild_id]
    
    def check_rate_limit(self, guild_id: int) -> bool:
        """Prüft Rate Limit für Server"""
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
        """Erweiterte Placeholder-Ersetzung mit Rückwärtskompatibilität"""
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
        """Sendet private Willkommensnachricht"""
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
        """Vergibt automatische Rolle"""
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
        """Event wird ausgelöst, wenn ein neuer User dem Server beitritt"""
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
        """Sendet Embed Welcome Message"""
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
        """Behandelt automatisches Löschen"""
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
    
    # Hauptbefehle - Reduziert auf 2 Commands
    welcome = discord.SlashCommandGroup("welcome", "Welcome System Verwaltung")
    
    @welcome.command(name="setup", description="Schritt-für-Schritt Welcome System Konfiguration")
    @commands.has_permissions(manage_guild=True)
    async def setup_welcome(self, ctx):
        """Verbessertes Setup mit Schritt-für-Schritt Ansatz"""
        
        # Aktuelle Einstellungen laden
        current_settings = await self.get_cached_settings(ctx.guild.id) or {}
        
        class WelcomeSetupView(discord.ui.View):
            def __init__(self, cog, current_settings):
                super().__init__(timeout=300)  # 5 Minuten
                self.cog = cog
                self.current_settings = current_settings
                self.setup_data = {}
                
            @discord.ui.button(label="🚀 Schnell-Setup", style=discord.ButtonStyle.green, emoji="🚀")
            async def quick_setup(self, button: discord.ui.Button, interaction: discord.Interaction):
                """Öffnet vereinfachtes Setup Modal"""
                modal = QuickSetupModal(self.cog, self.current_settings)
                await interaction.response.send_modal(modal)
                
            @discord.ui.button(label="⚙️ Erweitert", style=discord.ButtonStyle.primary, emoji="⚙️")
            async def advanced_setup(self, button: discord.ui.Button, interaction: discord.Interaction):
                """Startet erweiterte Konfiguration"""
                await self.start_advanced_setup(interaction)
                
            @discord.ui.button(label="📋 Vorlage", style=discord.ButtonStyle.secondary, emoji="📋")
            async def template_setup(self, button: discord.ui.Button, interaction: discord.Interaction):
                """Zeigt Template-Auswahl"""
                await self.show_templates(interaction)
                
            @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.danger, emoji="❌")
            async def cancel_setup(self, button: discord.ui.Button, interaction: discord.Interaction):
                embed = discord.Embed(
                    title="❌ Setup abgebrochen",
                    description="Die Konfiguration wurde abgebrochen.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                
            async def start_advanced_setup(self, interaction):
                """Startet erweiterte Schritt-für-Schritt Konfiguration"""
                self.setup_data = {}
                await self.step_1_channel(interaction)
                
            async def step_1_channel(self, interaction):
                """Schritt 1: Channel auswählen"""
                embed = discord.Embed(
                    title="🚀 Welcome Setup - Schritt 1/5",
                    description="**Channel auswählen**\n\nWähle den Channel, in dem Welcome Nachrichten gesendet werden sollen:",
                    color=discord.Color.blue()
                )
                
                # Channel Select Menu
                channel_select = ChannelSelect(self, step=1)
                view = discord.ui.View(timeout=300)
                view.add_item(channel_select)
                
                # Back/Cancel Buttons
                back_button = discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.danger)
                back_button.callback = self.cancel_setup
                view.add_item(back_button)
                
                if hasattr(interaction, 'response') and not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=view)
                else:
                    await interaction.edit_original_response(embed=embed, view=view)
                    
            async def step_2_role(self, interaction):
                """Schritt 2: Auto-Role (optional)"""
                embed = discord.Embed(
                    title="🚀 Welcome Setup - Schritt 2/5",
                    description="**Auto-Role (Optional)**\n\nSoll neuen Mitgliedern automatisch eine Rolle zugewiesen werden?",
                    color=discord.Color.blue()
                )
                
                view = discord.ui.View(timeout=300)
                
                # Role Select
                role_select = RoleSelect(self, step=2)
                view.add_item(role_select)
                
                # Skip Button
                skip_button = discord.ui.Button(label="⏭️ Überspringen", style=discord.ButtonStyle.secondary)
                skip_button.callback = lambda i: self.step_3_message_type(i)
                view.add_item(skip_button)
                
                # Back Button
                back_button = discord.ui.Button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
                back_button.callback = lambda i: self.step_1_channel(i)
                view.add_item(back_button)
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            async def step_3_message_type(self, interaction):
                """Schritt 3: Nachrichtentyp wählen"""
                embed = discord.Embed(
                    title="🚀 Welcome Setup - Schritt 3/5",
                    description="**Nachrichtentyp wählen**\n\nWie sollen Welcome Nachrichten angezeigt werden?",
                    color=discord.Color.blue()
                )
                
                view = discord.ui.View(timeout=300)
                
                # Text Message Button
                text_button = discord.ui.Button(label="📝 Einfache Nachricht", style=discord.ButtonStyle.primary)
                text_button.callback = lambda i: self.set_message_type(i, "text")
                view.add_item(text_button)
                
                # Embed Button
                embed_button = discord.ui.Button(label="🎨 Embed Nachricht", style=discord.ButtonStyle.primary)
                embed_button.callback = lambda i: self.set_message_type(i, "embed")
                view.add_item(embed_button)
                
                # Back Button
                back_button = discord.ui.Button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
                back_button.callback = lambda i: self.step_2_role(i)
                view.add_item(back_button)
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            async def set_message_type(self, interaction, msg_type):
                """Setzt Nachrichtentyp und geht zu Schritt 4"""
                self.setup_data['message_type'] = msg_type
                await self.step_4_features(interaction)
                
            async def step_4_features(self, interaction):
                """Schritt 4: Zusätzliche Features"""
                embed = discord.Embed(
                    title="🚀 Welcome Setup - Schritt 4/5",
                    description="**Zusätzliche Features**\n\nWelche zusätzlichen Features sollen aktiviert werden?",
                    color=discord.Color.blue()
                )
                
                view = discord.ui.View(timeout=300)
                
                # Feature Toggles
                features = [
                    ("dm", "💌 Private Nachricht senden", "Sendet zusätzlich eine private Nachricht"),
                    ("ping", "🔔 User erwähnen", "Erwähnt den User in der Welcome Nachricht"),
                    ("thumbnail", "🖼️ Avatar anzeigen", "Zeigt Avatar als Thumbnail (nur bei Embeds)")
                ]
                
                for key, label, description in features:
                    button = discord.ui.Button(
                        label=label,
                        style=discord.ButtonStyle.secondary,
                        emoji=label.split()[0]
                    )
                    button.callback = lambda i, k=key: self.toggle_feature(i, k)
                    view.add_item(button)
                
                # Continue Button
                continue_button = discord.ui.Button(label="➡️ Weiter", style=discord.ButtonStyle.success)
                continue_button.callback = lambda i: self.step_5_message(i)
                view.add_item(continue_button)
                
                # Back Button
                back_button = discord.ui.Button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
                back_button.callback = lambda i: self.step_3_message_type(i)
                view.add_item(back_button)
                
                # Show selected features
                selected_features = []
                for key in ['dm', 'ping', 'thumbnail']:
                    if self.setup_data.get(key, False):
                        feature_name = next(f[1] for f in features if f[0] == key)
                        selected_features.append(feature_name)
                
                if selected_features:
                    embed.add_field(
                        name="✅ Aktivierte Features",
                        value="\n".join(selected_features),
                        inline=False
                    )
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            async def toggle_feature(self, interaction, feature_key):
                """Toggle Feature an/aus"""
                current = self.setup_data.get(feature_key, False)
                self.setup_data[feature_key] = not current
                await self.step_4_features(interaction)
                
            async def step_5_message(self, interaction):
                """Schritt 5: Nachricht erstellen"""
                msg_type = self.setup_data.get('message_type', 'text')
                
                embed = discord.Embed(
                    title="🚀 Welcome Setup - Schritt 5/5",
                    description="**Welcome Nachricht erstellen**\n\nErstelle deine Welcome Nachricht oder wähle eine Vorlage:",
                    color=discord.Color.blue()
                )
                
                view = discord.ui.View(timeout=300)
                
                # Custom Message Button
                custom_button = discord.ui.Button(label="✏️ Eigene Nachricht", style=discord.ButtonStyle.primary)
                custom_button.callback = lambda i: self.create_custom_message(i)
                view.add_item(custom_button)
                
                # Template Buttons
                templates = ["basic", "fancy", "minimal", "detailed"]
                for template in templates:
                    template_button = discord.ui.Button(label=f"📋 {template.title()}", style=discord.ButtonStyle.secondary)
                    template_button.callback = lambda i, t=template: self.use_template(i, t)
                    view.add_item(template_button)
                
                # Back Button
                back_button = discord.ui.Button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
                back_button.callback = lambda i: self.step_4_features(i)
                view.add_item(back_button)
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            async def create_custom_message(self, interaction):
                """Öffnet Modal für eigene Nachricht"""
                msg_type = self.setup_data.get('message_type', 'text')
                modal = MessageModal(self, msg_type)
                await interaction.response.send_modal(modal)
                
            async def use_template(self, interaction, template_name):
                """Verwendet Template"""
                self.setup_data['template'] = template_name
                await self.finalize_setup(interaction)
                
            async def finalize_setup(self, interaction):
                """Finalisiert Setup"""
                try:
                    # Setup Daten in DB Format konvertieren
                    updates = {
                        'enabled': True,
                        'channel_id': self.setup_data.get('channel_id'),
                        'welcome_stats_enabled': True
                    }
                    
                    # Auto-Role
                    if self.setup_data.get('role_id'):
                        updates['auto_role_id'] = self.setup_data['role_id']
                    
                    # Message Type
                    if self.setup_data.get('message_type') == 'embed':
                        updates['embed_enabled'] = True
                        updates['embed_thumbnail'] = self.setup_data.get('thumbnail', False)
                    
                    # Features
                    updates['ping_user'] = self.setup_data.get('ping', False)
                    updates['join_dm_enabled'] = self.setup_data.get('dm', False)
                    
                    # Template oder Custom Message
                    if self.setup_data.get('template'):
                        template_data = self.get_template_data(self.setup_data['template'])
                        updates.update(template_data)
                    elif self.setup_data.get('custom_message'):
                        if updates.get('embed_enabled'):
                            updates['embed_description'] = self.setup_data['custom_message']
                        else:
                            updates['welcome_message'] = self.setup_data['custom_message']
                    
                    # In Datenbank speichern
                    success = await self.cog.db.update_welcome_settings(interaction.guild.id, **updates)
                    self.cog.invalidate_cache(interaction.guild.id)
                    
                    if success:
                        embed = await self.create_success_embed(interaction, updates)
                    else:
                        embed = discord.Embed(
                            title="❌ Setup fehlgeschlagen",
                            description="Die Konfiguration konnte nicht gespeichert werden.",
                            color=discord.Color.red()
                        )
                    
                    if hasattr(interaction, 'response') and not interaction.response.is_done():
                        await interaction.response.edit_message(embed=embed, view=None)
                    else:
                        await interaction.edit_original_response(embed=embed, view=None)
                        
                except Exception as e:
                    logger.error(f"Setup Finalize Error: {e}")
                    embed = discord.Embed(
                        title="❌ Setup Fehler",
                        description="Ein unerwarteter Fehler ist aufgetreten.",
                        color=discord.Color.red()
                    )
                    await interaction.edit_original_response(embed=embed, view=None)
                    
            def get_template_data(self, template_name):
                """Gibt Template Daten zurück"""
                templates = {
                    "basic": {
                        "welcome_message": "Willkommen %mention% auf **%servername%**! 🎉",
                        "embed_enabled": False,
                    },
                    "fancy": {
                        "embed_enabled": True,
                        "embed_title": "Willkommen auf %servername%! 🎉",
                        "embed_description": "Hey %user%! Du bist unser **%membercount%.** Mitglied!\n\nViel Spaß auf unserem Server! 🚀",
                        "embed_color": "#ff6b6b",
                        "embed_thumbnail": True,
                        "embed_footer": "Beigetreten am %joindate%",
                    },
                    "minimal": {
                        "welcome_message": "%user% ist dem Server beigetreten.",
                        "embed_enabled": False,
                    },
                    "detailed": {
                        "embed_enabled": True,
                        "embed_title": "🎊 Neues Mitglied!",
                        "embed_description": "**%mention%** ist **%servername%** beigetreten!\n\n👤 **Username:** %username%\n📅 **Account erstellt:** %createddate%\n📊 **Mitglied Nr.:** %membercount%\n⏰ **Beigetreten um:** %jointime%",
                        "embed_color": "#00d4ff",
                        "embed_thumbnail": True,
                        "embed_footer": "%servername% • %membercount% Mitglieder",
                    }
                }
                return templates.get(template_name, {})
                
            async def create_success_embed(self, interaction, updates):
                """Erstellt Erfolgs-Embed"""
                embed = discord.Embed(
                    title="✅ Welcome System erfolgreich konfiguriert!",
                    description="Das Welcome System wurde eingerichtet und ist jetzt aktiv.",
                    color=discord.Color.green()
                )
                
                # Channel
                channel = interaction.guild.get_channel(updates.get('channel_id'))
                embed.add_field(name="📢 Channel", value=channel.mention if channel else "Fehler", inline=True)
                
                # Auto-Role
                if updates.get('auto_role_id'):
                    role = interaction.guild.get_role(updates['auto_role_id'])
                    embed.add_field(name="🏷️ Auto-Role", value=role.mention if role else "Fehler", inline=True)
                
                # Message Type
                msg_type = "Embed" if updates.get('embed_enabled') else "Text"
                embed.add_field(name="🎨 Nachrichtentyp", value=msg_type, inline=True)
                
                # Features
                features = []
                if updates.get('join_dm_enabled'):
                    features.append("💌 Private Nachricht")
                if updates.get('ping_user'):
                    features.append("🔔 User erwähnen")
                if updates.get('embed_thumbnail'):
                    features.append("🖼️ Avatar Thumbnail")
                    
                if features:
                    embed.add_field(name="⚡ Features", value="\n".join(features), inline=False)
                
                embed.add_field(
                    name="🚀 Nächste Schritte",
                    value="• Verwende `/welcome test` um alles zu testen\n• Mit `/welcome message` kannst du die Nachricht bearbeiten\n• `/welcome info` zeigt alle verfügbaren Befehle",
                    inline=False
                )
                
                return embed
                
            async def show_templates(self, interaction):
                """Zeigt Template Übersicht"""
                embed = discord.Embed(
                    title="📋 Template Auswahl",
                    description="Wähle eine Vorlage für dein Welcome System:",
                    color=discord.Color.blue()
                )
                
                templates = {
                    "basic": ("🟢 Basic", "Einfache Text-Nachricht ohne Schnickschnack"),
                    "fancy": ("✨ Fancy", "Stylisches Embed mit Farben und Thumbnail"),
                    "minimal": ("⚪ Minimal", "Sehr einfache, unauffällige Nachricht"),
                    "detailed": ("📊 Detailed", "Ausführliches Embed mit vielen Informationen")
                }
                
                for template_id, (name, desc) in templates.items():
                    embed.add_field(name=name, value=desc, inline=False)
                
                view = discord.ui.View(timeout=300)
                
                for template_id in templates.keys():
                    button = discord.ui.Button(
                        label=templates[template_id][0].split()[1],  # Nur Name ohne Emoji
                        style=discord.ButtonStyle.primary
                    )
                    button.callback = lambda i, t=template_id: self.select_template_and_setup(i, t)
                    view.add_item(button)
                    
                # Back Button
                back_button = discord.ui.Button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
                back_button.callback = lambda i: self.show_main_menu(i)
                view.add_item(back_button)
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            async def select_template_and_setup(self, interaction, template_name):
                """Wählt Template und startet Mini-Setup"""
                # Minimales Setup für Template
                embed = discord.Embed(
                    title=f"📋 Template: {template_name.title()}",
                    description="Wähle nur noch den Welcome Channel aus:",
                    color=discord.Color.blue()
                )
                
                self.setup_data = {'template': template_name}
                
                view = discord.ui.View(timeout=300)
                channel_select = ChannelSelect(self, step="template")
                view.add_item(channel_select)
                
                back_button = discord.ui.Button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
                back_button.callback = lambda i: self.show_templates(i)
                view.add_item(back_button)
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            async def show_main_menu(self, interaction):
                """Zeigt Hauptmenü"""
                embed = discord.Embed(
                    title="🚀 Welcome System Setup",
                    description="Wähle eine Setup-Option:",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🚀 Schnell-Setup",
                    value="Grundkonfiguration mit einem Modal",
                    inline=False
                )
                
                embed.add_field(
                    name="⚙️ Erweiterte Konfiguration",
                    value="Schritt-für-Schritt durch alle Optionen",
                    inline=False
                )
                
                embed.add_field(
                    name="📋 Template verwenden",
                    value="Vorgefertigte Designs verwenden",
                    inline=False
                )
                
                await interaction.edit_original_response(embed=embed, view=self)

        class ChannelSelect(discord.ui.ChannelSelect):
            def __init__(self, setup_view, step):
                super().__init__(
                    placeholder="Wähle einen Text-Channel...",
                    channel_types=[discord.ChannelType.text],
                    max_values=1
                )
                self.setup_view = setup_view
                self.step = step
                
            async def callback(self, interaction: discord.Interaction):
                channel = self.values[0]
                self.setup_view.setup_data['channel_id'] = channel.id
                
                if self.step == 1:
                    await self.setup_view.step_2_role(interaction)
                elif self.step == "template":
                    # Template Setup finalisieren
                    await self.setup_view.finalize_setup(interaction)
                    
        class RoleSelect(discord.ui.RoleSelect):
            def __init__(self, setup_view, step):
                super().__init__(
                    placeholder="Wähle eine Rolle (optional)...",
                    max_values=1
                )
                self.setup_view = setup_view
                self.step = step
                
            async def callback(self, interaction: discord.Interaction):
                role = self.values[0]
                
                # Rolle Berechtigung prüfen
                if role >= interaction.guild.me.top_role:
                    embed = discord.Embed(
                        title="❌ Rolle zu hoch",
                        description=f"Die Rolle {role.mention} ist höher als meine höchste Rolle und kann nicht vergeben werden.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                    
                self.setup_view.setup_data['role_id'] = role.id
                await self.setup_view.step_3_message_type(interaction)

        class QuickSetupModal(discord.ui.Modal):
            def __init__(self, cog, current_settings):
                super().__init__(title="🚀 Schnell-Setup")
                self.cog = cog
                self.current_settings = current_settings
                
                # Channel Input
                self.channel_input = discord.ui.InputText(
                    label="Welcome Channel",
                    placeholder="#welcome oder Channel ID",
                    style=discord.InputTextStyle.short,
                    value=str(current_settings.get('channel_id', '')) if current_settings.get('channel_id') else '',
                    required=True,
                    max_length=100
                )
                self.add_item(self.channel_input)
                
                # Template Input
                self.template_input = discord.ui.InputText(
                    label="Vorlage (basic, fancy, minimal, detailed)",
                    placeholder="basic",
                    style=discord.InputTextStyle.short,
                    value="basic",
                    required=True,
                    max_length=20
                )
                self.add_item(self.template_input)
                
            async def callback(self, interaction: discord.Interaction):
                try:
                    # Channel parsen
                    channel_input = self.channel_input.value.strip()
                    channel = await self.parse_channel(interaction, channel_input)
                    if not channel:
                        return
                    
                    # Template laden
                    template_name = self.template_input.value.strip().lower()
                    if template_name not in ["basic", "fancy", "minimal", "detailed"]:
                        template_name = "basic"
                    
                    template_data = self.get_template_data(template_name)
                    template_data.update({
                        'enabled': True,
                        'channel_id': channel.id,
                        'welcome_stats_enabled': True,
                        'template_name': template_name
                    })
                    
                    success = await self.cog.db.update_welcome_settings(interaction.guild.id, **template_data)
                    self.cog.invalidate_cache(interaction.guild.id)
                    
                    if success:
                        embed = discord.Embed(
                            title="✅ Schnell-Setup erfolgreich!",
                            description=f"Welcome System mit Template '{template_name}' wurde eingerichtet.",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="📢 Channel", value=channel.mention, inline=True)
                        embed.add_field(name="📋 Template", value=template_name.title(), inline=True)
                        embed.add_field(
                            name="🚀 Nächste Schritte",
                            value="Verwende `/welcome test` zum Testen oder `/welcome message` zum Anpassen.",
                            inline=False
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Setup fehlgeschlagen",
                            description="Die Konfiguration konnte nicht gespeichert werden.",
                            color=discord.Color.red()
                        )
                    
                    await interaction.response.send_message(embed=embed)
                    
                except Exception as e:
                    logger.error(f"Quick Setup Error: {e}")
                    embed = discord.Embed(
                        title="❌ Fehler",
                        description="Ein Fehler ist beim Setup aufgetreten.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
            async def parse_channel(self, interaction, channel_input):
                """Channel aus Input parsen"""
                if channel_input.startswith('<#') and channel_input.endswith('>'):
                    channel_id = channel_input[2:-1]
                elif channel_input.startswith('#'):
                    channel = discord.utils.get(interaction.guild.text_channels, name=channel_input[1:])
                    if channel:
                        return channel
                    channel_id = None
                else:
                    channel_id = channel_input
                
                if channel_id and channel_id.isdigit():
                    channel = interaction.guild.get_channel(int(channel_id))
                    if channel and isinstance(channel, discord.TextChannel):
                        return channel
                
                embed = discord.Embed(
                    title="❌ Channel nicht gefunden",
                    description="Der angegebene Channel konnte nicht gefunden werden.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return None
                
            def get_template_data(self, template_name):
                """Template Daten"""
                templates = {
                    "basic": {
                        "welcome_message": "Willkommen %mention% auf **%servername%**! 🎉",
                        "embed_enabled": False,
                    },
                    "fancy": {
                        "embed_enabled": True,
                        "embed_title": "Willkommen auf %servername%! 🎉",
                        "embed_description": "Hey %user%! Du bist unser **%membercount%.** Mitglied!\n\nViel Spaß auf unserem Server! 🚀",
                        "embed_color": "#ff6b6b",
                        "embed_thumbnail": True,
                        "embed_footer": "Beigetreten am %joindate%",
                    },
                    "minimal": {
                        "welcome_message": "%user% ist dem Server beigetreten.",
                        "embed_enabled": False,
                    },
                    "detailed": {
                        "embed_enabled": True,
                        "embed_title": "🎊 Neues Mitglied!",
                        "embed_description": "**%mention%** ist **%servername%** beigetreten!\n\n👤 **Username:** %username%\n📅 **Account erstellt:** %createddate%\n📊 **Mitglied Nr.:** %membercount%\n⏰ **Beigetreten um:** %jointime%",
                        "embed_color": "#00d4ff",
                        "embed_thumbnail": True,
                        "embed_footer": "%servername% • %membercount% Mitglieder",
                    }
                }
                return templates.get(template_name, templates["basic"])

        class MessageModal(discord.ui.Modal):
            def __init__(self, setup_view, msg_type):
                super().__init__(title="Welcome Nachricht erstellen")
                self.setup_view = setup_view
                self.msg_type = msg_type
                
                if msg_type == "embed":
                    self.message_input = discord.ui.InputText(
                        label="Embed Beschreibung",
                        placeholder="Hey %mention%! Willkommen auf %servername%! Du bist unser %membercount%. Mitglied!",
                        style=discord.InputTextStyle.long,
                        required=True,
                        max_length=2048
                    )
                else:
                    self.message_input = discord.ui.InputText(
                        label="Welcome Nachricht",
                        placeholder="Willkommen %mention% auf **%servername%**! 🎉",
                        style=discord.InputTextStyle.long,
                        required=True,
                        max_length=2000
                    )
                
                self.add_item(self.message_input)
                
            async def callback(self, interaction: discord.Interaction):
                self.setup_view.setup_data['custom_message'] = self.message_input.value
                await self.setup_view.finalize_setup(interaction)

        # Setup View anzeigen
        embed = discord.Embed(
            title="🚀 Welcome System Setup",
            description="Wähle eine Setup-Option um zu beginnen:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🚀 Schnell-Setup",
            value="Schnelle Grundkonfiguration mit Template",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Erweiterte Konfiguration",
            value="Schritt-für-Schritt durch alle Optionen",
            inline=False
        )
        
        embed.add_field(
            name="📋 Template verwenden",
            value="Vorgefertigte Designs direkt anwenden",
            inline=False
        )
        
        # Aktuelle Konfiguration anzeigen falls vorhanden
        if current_settings and current_settings.get('enabled'):
            channel = ctx.bot.get_channel(current_settings.get('channel_id'))
            embed.add_field(
                name="ℹ️ Aktuelle Konfiguration",
                value=f"Channel: {channel.mention if channel else 'Nicht gesetzt'}\nStatus: {'Aktiv' if current_settings.get('enabled') else 'Inaktiv'}",
                inline=False
            )
        
        view = WelcomeSetupView(self, current_settings)
        await ctx.respond(embed=embed, view=view)


    @welcome.command(name="message", description="Setzt die Welcome Message über ein Modal")
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_message(self, ctx):
        """Öffnet ein Modal zum Setzen der Welcome Message"""
        
        # Aktuelle Einstellungen laden für Vorausfüllung
        current_settings = await self.get_cached_settings(ctx.guild.id)
        
        if not current_settings:
            embed = discord.Embed(
                title="❌ Keine Konfiguration gefunden",
                description="Verwende zuerst `/welcome setup` um das Welcome System zu konfigurieren.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        current_message = current_settings.get('welcome_message', '')
        is_embed_mode = current_settings.get('embed_enabled', False)
        
        class WelcomeMessageModal(discord.ui.Modal):
            def __init__(self, cog, current_msg="", embed_mode=False, current_settings=None):
                super().__init__(title="Welcome Message konfigurieren")
                self.cog = cog
                self.embed_mode = embed_mode
                self.current_settings = current_settings or {}
                
                if embed_mode:
                    # Embed Titel
                    self.title_input = discord.ui.InputText(
                        label="Embed Titel (Optional)",
                        placeholder="z.B: Willkommen auf %servername%!",
                        style=discord.InputTextStyle.short,
                        value=self.current_settings.get('embed_title', ''),
                        required=False,
                        max_length=256
                    )
                    self.add_item(self.title_input)
                    
                    # Embed Beschreibung
                    self.description_input = discord.ui.InputText(
                        label="Embed Beschreibung",
                        placeholder="Hey %mention%! Du bist unser %membercount%. Mitglied!",
                        style=discord.InputTextStyle.long,
                        value=self.current_settings.get('embed_description', current_msg),
                        required=True,
                        max_length=2048
                    )
                    self.add_item(self.description_input)
                    
                    # Embed Footer
                    self.footer_input = discord.ui.InputText(
                        label="Embed Footer (Optional)",
                        placeholder="z.B: Beigetreten am %joindate%",
                        style=discord.InputTextStyle.short,
                        value=self.current_settings.get('embed_footer', ''),
                        required=False,
                        max_length=2048
                    )
                    self.add_item(self.footer_input)
                    
                    # Embed Farbe
                    self.color_input = discord.ui.InputText(
                        label="Embed Farbe (Hex-Code)",
                        placeholder="z.B: #ff6b6b oder #00d4ff",
                        style=discord.InputTextStyle.short,
                        value=self.current_settings.get('embed_color', '#00ff00'),
                        required=False,
                        max_length=7
                    )
                    self.add_item(self.color_input)
                else:
                    # Normale Nachricht
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
                try:
                    updates = {}
                    
                    if self.embed_mode:
                        # Embed Einstellungen
                        if hasattr(self, 'title_input') and self.title_input.value.strip():
                            updates['embed_title'] = self.title_input.value.strip()
                        
                        if hasattr(self, 'description_input') and self.description_input.value.strip():
                            updates['embed_description'] = self.description_input.value.strip()
                        
                        if hasattr(self, 'footer_input') and self.footer_input.value.strip():
                            updates['embed_footer'] = self.footer_input.value.strip()
                        
                        if hasattr(self, 'color_input') and self.color_input.value.strip():
                            color = self.color_input.value.strip()
                            if not color.startswith('#'):
                                color = '#' + color
                            updates['embed_color'] = color
                        
                        message_text = updates.get('embed_description', 'Embed Message')
                    else:
                        # Normale Message
                        message = self.message_input.value.strip()
                        if not message:
                            embed = discord.Embed(
                                title="❌ Fehler",
                                description="Die Welcome Message darf nicht leer sein.",
                                color=discord.Color.red()
                            )
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                        
                        updates['welcome_message'] = message
                        message_text = message
                    
                    success = await self.cog.db.update_welcome_settings(interaction.guild.id, **updates)
                    self.cog.invalidate_cache(interaction.guild.id)
                    
                    if success:
                        # Vorschau erstellen
                        preview = self.cog.replace_placeholders(message_text, interaction.user, interaction.guild)
                        
                        embed = discord.Embed(
                            title="✅ Welcome Message aktualisiert",
                            color=discord.Color.green()
                        )
                        
                        embed.add_field(
                            name="💬 Neue Message",
                            value=f"```{message_text[:400]}{'...' if len(message_text) > 400 else ''}```",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="👀 Vorschau (mit deinen Daten)",
                            value=preview[:400] + ("..." if len(preview) > 400 else ""),
                            inline=False
                        )
                        
                        if self.embed_mode:
                            embed.add_field(
                                name="🎨 Modus",
                                value="Embed-Nachricht",
                                inline=True
                            )
                        
                        embed.add_field(
                            name="💡 Tipp",
                            value="Verwende `/welcome test` für eine vollständige Vorschau oder `/welcome info` für alle Befehle.",
                            inline=False
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Fehler",
                            description="Die Welcome Message konnte nicht gesetzt werden.",
                            color=discord.Color.red()
                        )
                    
                    await interaction.response.send_message(embed=embed)
                    
                except Exception as e:
                    logger.error(f"Message Modal Error: {e}")
                    embed = discord.Embed(
                        title="❌ Fehler",
                        description="Ein unerwarteter Fehler ist aufgetreten.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
        
        modal = WelcomeMessageModal(self, current_message, is_embed_mode, current_settings)
        await ctx.send_modal(modal)
    
    # Utility Commands - Kombiniert in wenige Befehle
    @welcome.command(name="info", description="Zeigt alle Informationen und verfügbare Befehle")
    @commands.has_permissions(manage_messages=True)
    async def welcome_info(self, ctx, show_type: discord.Option(str, choices=["config", "placeholders", "templates", "commands"], required=False) = "commands"):
        """Zeigt verschiedene Informationen zum Welcome System"""
        
        if show_type == "config":
            # Aktuelle Konfiguration anzeigen
            settings = await self.get_cached_settings(ctx.guild.id)
            
            if not settings:
                embed = discord.Embed(
                    title="❌ Keine Konfiguration gefunden",
                    description="Es sind noch keine Welcome Einstellungen vorhanden. Verwende `/welcome setup` zum Einrichten.",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            channel = self.bot.get_channel(settings.get('channel_id')) if settings.get('channel_id') else None
            auto_role = ctx.guild.get_role(settings.get('auto_role_id')) if settings.get('auto_role_id') else None
            
            embed = discord.Embed(
                title="⚙️ Welcome System Konfiguration",
                color=discord.Color.blue()
            )
            
            # Basis Einstellungen
            embed.add_field(
                name="📊 Status",
                value="✅ Aktiviert" if settings.get('enabled') else "❌ Deaktiviert",
                inline=True
            )
            
            embed.add_field(
                name="📢 Channel",
                value=channel.mention if channel else "❌ Nicht gesetzt",
                inline=True
            )
            
            embed.add_field(
                name="🎨 Modus",
                value="Embed" if settings.get('embed_enabled') else "Text",
                inline=True
            )
            
            if auto_role:
                embed.add_field(
                    name="🏷️ Auto-Role",
                    value=auto_role.mention,
                    inline=True
                )
            
            if settings.get('join_dm_enabled'):
                embed.add_field(
                    name="💌 Private Nachricht",
                    value="✅ Aktiviert",
                    inline=True
                )
            
            if settings.get('template_name'):
                embed.add_field(
                    name="📋 Vorlage",
                    value=settings.get('template_name').title(),
                    inline=True
                )
            
            # Welcome Message Vorschau
            if settings.get('embed_enabled'):
                message_preview = settings.get('embed_description', 'Embed-Nachricht')
            else:
                message_preview = settings.get('welcome_message', 'Nicht gesetzt')
            
            if message_preview and len(message_preview) > 100:
                message_preview = message_preview[:100] + "..."
            
            embed.add_field(
                name="💬 Welcome Message",
                value=f"```{message_preview}```",
                inline=False
            )
            
        elif show_type == "placeholders":
            # Placeholder anzeigen
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
                    "`%userid%` - User ID"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🏠 Server Informationen",
                value=(
                    "`%servername%` - Servername\n"
                    "`%membercount%` - Mitgliederanzahl\n"
                    "`%onlinemembers%` - Online Mitglieder"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⏰ Zeit & Datum",
                value=(
                    "`%joindate%` - Beitrittsdatum\n"
                    "`%jointime%` - Beitrittszeit\n"
                    "`%createddate%` - Account Erstellung\n"
                    "`%accountage%` - Account Alter"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎭 Erweiterte Informationen",
                value=(
                    "`%roles%` - Alle Rollen\n"
                    "`%highestrole%` - Höchste Rolle\n"
                    "`%avatar%` - Avatar URL"
                ),
                inline=False
            )
            
            embed.set_footer(text="Beispiel: Willkommen %mention%! Du bist Mitglied #%membercount%")
            
        elif show_type == "templates":
            # Templates anzeigen
            embed = discord.Embed(
                title="📋 Verfügbare Vorlagen",
                description="Diese Vorlagen können in `/welcome setup` verwendet werden:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🟢 basic",
                value="Einfache Text-Nachricht\n*Willkommen @User auf Server!*",
                inline=True
            )
            
            embed.add_field(
                name="✨ fancy",
                value="Stylishes Embed mit Farben\n*Embed mit Thumbnail und Footer*",
                inline=True
            )
            
            embed.add_field(
                name="⚪ minimal",
                value="Minimale Nachricht\n*User ist beigetreten.*",
                inline=True
            )
            
            embed.add_field(
                name="📊 detailed",
                value="Detailliertes Embed\n*Mit vielen Statistiken*",
                inline=True
            )
            
            embed.add_field(
                name="💡 Verwendung",
                value="Gib einfach den Vorlagennamen in `/welcome setup` ein!",
                inline=False
            )
            
        else:  # commands
            # Befehle anzeigen
            embed = discord.Embed(
                title="🤖 Welcome System Befehle",
                description="Alle verfügbaren Welcome System Befehle:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="⚙️ Setup & Verwaltung",
                value=(
                    "`/welcome setup` - Vollständige Konfiguration\n"
                    "`/welcome message` - Nachricht bearbeiten\n"
                    "`/welcome info config` - Aktuelle Einstellungen"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📚 Informationen",
                value=(
                    "`/welcome info placeholders` - Alle Placeholder\n"
                    "`/welcome info templates` - Verfügbare Vorlagen\n"
                    "`/welcome test` - System testen"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📊 Verwaltung",
                value=(
                    "`/welcome manage toggle` - System ein/aus\n"
                    "`/welcome manage stats` - Statistiken\n"
                    "`/welcome manage reset` - Zurücksetzen"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💡 Erste Schritte",
                value="1️⃣ Verwende `/welcome setup` für die Einrichtung\n2️⃣ Setze mit `/welcome message` deine Nachricht\n3️⃣ Teste mit `/welcome test`",
                inline=False
            )
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @welcome.command(name="test", description="Testet die Welcome Message")
    @commands.has_permissions(manage_messages=True)
    async def test_welcome(self, ctx):
        """Testet die Welcome Message mit dem aktuellen User"""
        settings = await self.get_cached_settings(ctx.guild.id)
        
        if not settings:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Es sind noch keine Welcome Einstellungen vorhanden. Verwende `/welcome setup`.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if not settings.get('channel_id'):
            embed = discord.Embed(
                title="❌ Fehler",
                description="Es ist kein Welcome Channel gesetzt.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        # Test Embed erstellen
        member = ctx.author
        
        embed = discord.Embed(
            title="🧪 Welcome Message Test",
            description=f"So würde die Welcome Message für {member.mention} aussehen:",
            color=discord.Color.blue()
        )
        
        if settings.get('embed_enabled'):
            # Embed Mode Test
            embed.add_field(name="🎨 Modus", value="Embed-Nachricht", inline=True)
            
            test_embed_title = settings.get('embed_title', '')
            if test_embed_title:
                processed_title = self.replace_placeholders(test_embed_title, member, ctx.guild)
                embed.add_field(name="📋 Titel", value=processed_title, inline=False)
            
            test_embed_desc = settings.get('embed_description', '')
            if test_embed_desc:
                processed_desc = self.replace_placeholders(test_embed_desc, member, ctx.guild)
                embed.add_field(name="📄 Beschreibung", value=processed_desc[:400] + ("..." if len(processed_desc) > 400 else ""), inline=False)
            
            test_embed_footer = settings.get('embed_footer', '')
            if test_embed_footer:
                processed_footer = self.replace_placeholders(test_embed_footer, member, ctx.guild)
                embed.add_field(name="📝 Footer", value=processed_footer, inline=False)
                
        else:
            # Text Mode Test
            embed.add_field(name="🎨 Modus", value="Text-Nachricht", inline=True)
            
            welcome_message = settings.get('welcome_message', 'Willkommen %mention% auf **%servername%**!')
            processed_message = self.replace_placeholders(welcome_message, member, ctx.guild)
            embed.add_field(name="📄 Nachricht", value=processed_message[:400] + ("..." if len(processed_message) > 400 else ""), inline=False)
        
        # Zusätzliche Features
        features = []
        if settings.get('auto_role_id'):
            auto_role = ctx.guild.get_role(settings.get('auto_role_id'))
            features.append(f"🏷️ Auto-Role: {auto_role.mention if auto_role else 'Rolle nicht gefunden'}")
        
        if settings.get('join_dm_enabled'):
            features.append("💌 Private Nachricht würde gesendet")
        
        if settings.get('embed_thumbnail'):
            features.append("🖼️ Avatar als Thumbnail")
        
        if settings.get('ping_user'):
            features.append("🔔 User wird gepingt")
        
        if features:
            embed.add_field(name="⚡ Aktive Features", value="\n".join(features), inline=False)
        
        channel = self.bot.get_channel(settings.get('channel_id'))
        embed.set_footer(text=f"Nachricht würde in #{channel.name if channel else 'Channel nicht gefunden'} gesendet")
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    manage = discord.SlashCommandGroup("manage", "Welcome System Verwaltung")
    
    @manage.command(name="toggle", description="Schaltet das Welcome System ein/aus")
    @commands.has_permissions(manage_guild=True)
    async def toggle_welcome(self, ctx):
        """Schaltet das Welcome System ein oder aus"""
        new_state = await self.db.toggle_welcome(ctx.guild.id)
        self.invalidate_cache(ctx.guild.id)
        
        if new_state is None:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Es sind noch keine Welcome Einstellungen vorhanden. Verwende `/welcome setup`.",
                color=discord.Color.red()
            )
        else:
            status = "aktiviert" if new_state else "deaktiviert"
            embed = discord.Embed(
                title=f"✅ Welcome System {status}",
                description=f"Das Welcome System wurde **{status}**.",
                color=discord.Color.green() if new_state else discord.Color.orange()
            )
        
        await ctx.respond(embed=embed)
    
    @manage.command(name="stats", description="Zeigt Welcome Statistiken")
    @commands.has_permissions(manage_messages=True)
    async def show_stats(self, ctx):
        """Zeigt Welcome Statistiken für den Server"""
        try:
            await self.db.migrate_database()
            
            # Statistiken aktivieren falls noch nicht geschehen
            settings = await self.get_cached_settings(ctx.guild.id)
            if settings and not settings.get('welcome_stats_enabled'):
                await self.db.update_welcome_settings(ctx.guild.id, welcome_stats_enabled=True)
                self.invalidate_cache(ctx.guild.id)
            
            # Statistiken aus DB holen
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
                    value=f"👋 **{today_joins}** beigetreten\n🚪 **{today_leaves}** verlassen",
                    inline=True
                )
                
                # Diese Woche
                week_joins = week_stats[0] if week_stats and week_stats[0] else 0
                week_leaves = week_stats[1] if week_stats and week_stats[1] else 0
                embed.add_field(
                    name="📅 Diese Woche",
                    value=f"👋 **{week_joins}** beigetreten\n🚪 **{week_leaves}** verlassen",
                    inline=True
                )
                
                # Gesamt
                total_joins = total_stats[0] if total_stats and total_stats[0] else 0
                total_leaves = total_stats[1] if total_stats and total_stats[1] else 0
                embed.add_field(
                    name="📊 Gesamt",
                    value=f"👋 **{total_joins}** beigetreten\n🚪 **{total_leaves}** verlassen",
                    inline=True
                )
                
                # Server Info
                embed.add_field(
                    name="ℹ️ Server Info",
                    value=f"👥 **Aktuelle Mitglieder:** {ctx.guild.member_count}\n📈 **Netto Wachstum:** +{total_joins - total_leaves}",
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
    
    @manage.command(name="reset", description="Setzt alle Welcome Einstellungen zurück")
    @commands.has_permissions(administrator=True)
    async def reset_welcome(self, ctx):
        """Setzt alle Welcome Einstellungen zurück"""
        
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.confirmed = False
            
            @discord.ui.button(label="✅ Ja, zurücksetzen", style=discord.ButtonStyle.danger)
            async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
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
        """Tracking für Member Leaves"""
        try:
            settings = await self.get_cached_settings(member.guild.id)
            if settings and settings.get('welcome_stats_enabled'):
                await self.db.update_welcome_stats(member.guild.id, leaves=1)
        except Exception as e:
            logger.error(f"Leave Stats Error: {e}")


def setup(bot):
    bot.add_cog(WelcomeSystem(bot))