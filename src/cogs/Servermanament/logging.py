# Copyright (c) 2025 OPPRO.NET Network
# File: logging_cog.py

import discord
from discord import SlashCommandGroup
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List
import asyncio
import logging

# Import our separate database class
from DevTools import LoggingDatabase

# Setup logging
logger = logging.getLogger(__name__)

class LoggingCog(commands.Cog):
    """
    Comprehensive Discord logging system with improved performance and features
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.db = LoggingDatabase()

        # Improved caching system
        self._edit_tasks: Dict[int, asyncio.Task] = {}
        self._bulk_deletes: Dict[int, Dict[str, any]] = {}
        self._voice_cache: Dict[int, Dict[int, Optional[discord.VoiceState]]] = {}
        
        # Configuration
        self.config = {
            'edit_debounce_time': 3.0,      # Sekunden
            'bulk_delete_threshold': 3,     # Anzahl für Bulk-Erkennung
            'bulk_delete_window': 2.0,      # Sekunden Zeitfenster
            'max_content_length': 1500,     # Max Content-Länge in Embeds
            'max_embed_fields': 25,         # Discord Limit
            'cleanup_interval': 300,        # 5 Minuten Cache-Cleanup
            'max_attachment_display': 5,    # Max Attachments in Embed
            'max_role_display': 10,         # Max Roles in Embed
        }
        
        # Performance tracking
        self._stats = {
            'events_processed': 0,
            'logs_sent': 0,
            'errors': 0,
            'cache_hits': 0,
            'startup_time': datetime.utcnow(),
        }

        # Start background tasks
        self._cleanup_task = None
        self.bot.loop.create_task(self._start_background_tasks())
        
        logger.info("LoggingCog initialized successfully")

    async def _start_background_tasks(self):
        """Startet Background-Tasks nachdem der Bot bereit ist"""
        await self.bot.wait_until_ready()
        self._cleanup_task = self.bot.loop.create_task(self._cleanup_loop())
        logger.info("Background tasks started")

    def cog_unload(self):
        """Cleanup beim Entladen der Cog"""
        logger.info("Unloading LoggingCog...")
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        # Cancel all edit tasks
        for task in self._edit_tasks.values():
            if not task.done():
                task.cancel()
        
        # Close database connection
        self.db.close()
        logger.info("LoggingCog unloaded successfully")

    async def _cleanup_loop(self):
        """Regelmäßige Cache-Bereinigung mit verbesserter Logik"""
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(self.config['cleanup_interval'])
                await self._cleanup_caches()
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                self._stats['errors'] += 1

    async def _cleanup_caches(self):
        """Bereinigt alle Caches"""
        try:
            cleanup_count = 0
            
            # Edit Tasks bereinigen
            completed_tasks = [
                msg_id for msg_id, task in self._edit_tasks.items()
                if task.done()
            ]
            for msg_id in completed_tasks:
                del self._edit_tasks[msg_id]
                cleanup_count += 1

            # Bulk Delete Cache bereinigen (älter als 5 Minuten)
            current_time = datetime.utcnow()
            expired_guilds = []
            
            for guild_id, data in self._bulk_deletes.items():
                if 'timestamp' in data:
                    age = (current_time - data['timestamp']).total_seconds()
                    if age > 300:  # 5 Minuten
                        expired_guilds.append(guild_id)
            
            for guild_id in expired_guilds:
                del self._bulk_deletes[guild_id]
                cleanup_count += 1

            # Voice Cache für offline Mitglieder bereinigen
            for guild_id in list(self._voice_cache.keys()):
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    del self._voice_cache[guild_id]
                    cleanup_count += 1
                    continue
                
                offline_members = []
                for member_id in self._voice_cache[guild_id]:
                    member = guild.get_member(member_id)
                    if not member or not member.voice:
                        offline_members.append(member_id)
                
                for member_id in offline_members:
                    del self._voice_cache[guild_id][member_id]
                    cleanup_count += 1

            if cleanup_count > 0:
                logger.debug(f"Cache cleanup: {cleanup_count} items removed")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            self._stats['errors'] += 1

    async def send_log(self, guild_id: int, embed: discord.Embed, log_type: str = "general") -> bool:
        """Verbesserte Log-Versendung mit Retry-Logik"""
        try:
            channel_id = await self.db.get_log_channel(guild_id, log_type)
            if not channel_id:
                return False

            channel = self.bot.get_channel(channel_id)
            if not channel:
                # Channel nicht mehr vorhanden, aus DB entfernen
                await self.db.remove_log_channel(guild_id, log_type)
                logger.warning(f"Removed invalid channel {channel_id} for guild {guild_id}")
                return False

            # Embed validieren und anpassen
            if len(embed) > 6000:  # Discord Limit
                embed.description = "⚠️ Inhalt zu lang für Anzeige"
                # Felder reduzieren falls nötig
                while len(embed.fields) > 10:
                    embed.remove_field(-1)

            # Embed senden
            await channel.send(embed=embed)
            self._stats['logs_sent'] += 1
            return True

        except discord.Forbidden:
            logger.warning(f"No permission for log channel in guild {guild_id}")
            await self.db.remove_log_channel(guild_id, log_type)
            return False
        except discord.NotFound:
            logger.warning(f"Log channel not found in guild {guild_id}")
            await self.db.remove_log_channel(guild_id, log_type)
            return False
        except discord.HTTPException as e:
            if e.code == 50035:  # Invalid form body
                logger.error(f"Invalid embed content for guild {guild_id}: {e}")
                # Fallback embed senden
                try:
                    fallback_embed = discord.Embed(
                        title="⚠️ Log-Fehler",
                        description="Originale Log-Nachricht konnte nicht angezeigt werden (zu lang oder ungültig)",
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    await channel.send(embed=fallback_embed)
                except:
                    pass
            else:
                logger.error(f"HTTP error sending log to guild {guild_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending log to guild {guild_id}: {e}")
            self._stats['errors'] += 1

        return False

    def _create_user_embed(self, title: str, user: discord.User, color: discord.Color,
                           extra_fields: Dict[str, str] = None, 
                           description: str = None) -> discord.Embed:
        """Verbesserte User-Embed Erstellung"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )

        # User Info - immer als erstes
        embed.add_field(
            name="👤 User", 
            value=f"{user.mention}\n`{user}`", 
            inline=True
        )
        embed.add_field(
            name="🆔 ID", 
            value=f"`{user.id}`", 
            inline=True
        )
        embed.add_field(
            name="📅 Erstellt", 
            value=f"<t:{int(user.created_at.timestamp())}:R>", 
            inline=True
        )

        # Extra Felder hinzufügen
        if extra_fields:
            for name, value in extra_fields.items():
                if len(embed.fields) < self.config['max_embed_fields']:
                    embed.add_field(name=name, value=str(value)[:1000], inline=True)

        # Avatar und Footer
        if user.display_avatar:
            embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.set_footer(text=f"User ID: {user.id}")
        return embed

    def _truncate_content(self, content: str, max_length: int = None) -> str:
        """Kürzt Content intelligent"""
        if not content:
            return "*Leer*"
        
        max_length = max_length or self.config['max_content_length']
        
        if len(content) <= max_length:
            return content
        
        # An Wort-Grenzen kürzen wenn möglich
        truncated = content[:max_length-3]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # Nur wenn nicht zu viel verloren geht
            truncated = truncated[:last_space]
        
        return f"{truncated}..."

    def _format_content_for_embed(self, content: str, escape_markdown: bool = True) -> str:
        """Formatiert Content sicher für Embeds"""
        if not content:
            return "*Leer*"
        
        content = self._truncate_content(content)
        
        if escape_markdown:
            # Escape problematische Zeichen
            content = content.replace("```", "'''")
            content = content.replace("`", "'")
        
        return f"```\n{content}\n```"

    # =============================================================================
    # SLASH COMMANDS - Improved
    # =============================================================================

    logging = SlashCommandGroup("logging", description="Setze die Logging Systeme")

    @logging.command(name="channel", description="Setzt den Log-Channel für verschiedene Events")
    @discord.default_permissions(administrator=True)
    async def set_log_channel(self, ctx, 
                              channel: discord.TextChannel,
                              log_type: discord.Option(str, 
                                                       choices=["general", "moderation", "voice", "messages", "all"],
                                                       description="Art der Logs", 
                                                       default="general")):
        """Verbesserte Log-Channel Konfiguration"""
        try:
            # Berechtigungen prüfen
            perms = channel.permissions_for(ctx.guild.me)
            if not perms.send_messages:
                embed = discord.Embed(
                    title="❌ Keine Berechtigung",
                    description=f"Ich kann keine Nachrichten in {channel.mention} senden.",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            if not perms.embed_links:
                embed = discord.Embed(
                    title="⚠️ Fehlende Berechtigung",
                    description=f"Ich benötige die 'Embed Links' Berechtigung in {channel.mention}.",
                    color=discord.Color.orange()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            if log_type == "all":
                # Alle Log-Typen setzen
                types = ["general", "moderation", "voice", "messages"]
                for lt in types:
                    await self.db.set_log_channel(ctx.guild.id, channel.id, lt)
                
                embed = discord.Embed(
                    title="✅ Alle Log-Channels gesetzt",
                    description=f"Alle Logs werden nun in {channel.mention} gesendet.\n\n" +
                               f"**Konfigurierte Typen:** {', '.join(types)}",
                    color=discord.Color.green()
                )
            else:
                await self.db.set_log_channel(ctx.guild.id, channel.id, log_type)
                
                embed = discord.Embed(
                    title="✅ Log-Channel gesetzt",
                    description=f"**{log_type.title()}**-Logs werden nun in {channel.mention} gesendet.",
                    color=discord.Color.green()
                )

            embed.set_footer(text=f"Konfiguriert von {ctx.author}")
            await ctx.respond(embed=embed, ephemeral=True)

            # Test-Nachricht senden
            test_embed = discord.Embed(
                title="🧪 Test-Nachricht",
                description=f"Log-Channel für **{log_type}** erfolgreich konfiguriert!",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            test_embed.set_footer(text="Dies ist eine Test-Nachricht")
            await self.send_log(ctx.guild.id, test_embed, "general" if log_type == "all" else log_type)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Setzen des Log-Channels:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            logger.error(f"Error in set_log_channel: {e}")

    @logging.command(name="remove", description="Entfernt einen Log-Channel")
    @discord.default_permissions(administrator=True)
    async def remove_log_channel(self, ctx,
                                 log_type: discord.Option(str,
                                                          choices=["general", "moderation", "voice", "messages", "all"],
                                                          description="Art der Logs", default="all")):
        """Entfernt Log-Channel Konfiguration"""
        try:
            if log_type == "all":
                deleted_count = await self.db.remove_all_log_channels(ctx.guild.id)
                description = f"Alle Log-Channels wurden entfernt. ({deleted_count} Einträge)"
            else:
                deleted_count = await self.db.remove_log_channel(ctx.guild.id, log_type)
                if deleted_count > 0:
                    description = f"{log_type.title()}-Logging wurde deaktiviert."
                else:
                    description = f"Kein {log_type.title()}-Logging war konfiguriert."

            embed = discord.Embed(
                title="🗑️ Log-Channel entfernt",
                description=description,
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Entfernt von {ctx.author}")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Entfernen des Log-Channels:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            logger.error(f"Error in remove_log_channel: {e}")

    @logging.command(name="status", description="Zeigt die aktuellen Log-Einstellungen")
    @discord.default_permissions(administrator=True)
    async def log_status(self, ctx):
        """Verbesserter Log-Status mit mehr Details"""
        try:
            channels = await self.db.get_all_log_channels(ctx.guild.id)
            stats = await self.db.get_statistics()

            embed = discord.Embed(
                title="📊 Logging Status",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            if not channels:
                embed.description = "❌ Keine Log-Channels konfiguriert."
                embed.add_field(
                    name="💡 Tipp", 
                    value="Nutze `/setlogchannel` um Logging zu aktivieren.", 
                    inline=False
                )
            else:
                status_text = f"✅ **{len(channels)}** Log-Typ(en) konfiguriert\n\n"
                
                for log_type, channel_id in channels.items():
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        status_text += f"**{log_type.title()}:** {channel.mention}\n"
                    else:
                        status_text += f"**{log_type.title()}:** ❌ *Channel nicht gefunden* (`{channel_id}`)\n"
                
                embed.description = status_text

            # Bot Statistiken
            uptime = datetime.utcnow() - self._stats['startup_time']
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds%3600)//60}m"
            
            embed.add_field(
                name="📈 Cog Statistiken", 
                value=f"Events verarbeitet: **{self._stats['events_processed']:,}**\n" +
                      f"Logs gesendet: **{self._stats['logs_sent']:,}**\n" +
                      f"Fehler: **{self._stats['errors']}**\n" +
                      f"Uptime: **{uptime_str}**", 
                inline=True
            )

            # Cache Info
            voice_cache_size = sum(len(vc) for vc in self._voice_cache.values())
            embed.add_field(
                name="🗄️ Cache Status", 
                value=f"Edit Tasks: **{len(self._edit_tasks)}**\n" +
                      f"Bulk Deletes: **{len(self._bulk_deletes)}**\n" +
                      f"Voice Cache: **{voice_cache_size}**", 
                inline=True
            )

            # Datenbank Statistiken
            if stats:
                embed.add_field(
                    name="🗃️ Datenbank", 
                    value=f"Aktive Channels: **{stats.get('enabled_entries', 0)}**\n" +
                          f"Guilds mit Logging: **{stats.get('unique_guilds', 0)}**\n" +
                          f"Einzigartige Channels: **{stats.get('unique_channels', 0)}**", 
                    inline=True
                )

            embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Abrufen des Status:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            logger.error(f"Error in log_status: {e}")

    @logging.command(name="backup", description="Erstellt ein Backup der Log-Konfiguration")
    @discord.default_permissions(administrator=True)
    async def log_backup(self, ctx):
        """Erstellt ein Datenbank-Backup"""
        try:
            backup_path = f"data/log_channels_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
            success = await self.db.backup_database(backup_path)
            
            if success:
                embed = discord.Embed(
                    title="✅ Backup erstellt",
                    description=f"Datenbank-Backup wurde erfolgreich erstellt:\n`{backup_path}`",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Backup fehlgeschlagen",
                    description="Backup konnte nicht erstellt werden. Prüfe die Logs für Details.",
                    color=discord.Color.red()
                )
            
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Backup:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            logger.error(f"Error in log_backup: {e}")

    # =============================================================================
    # EVENT HANDLERS - Enhanced
    # =============================================================================

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Verbessertes Member Join Logging"""
        try:
            self._stats['events_processed'] += 1
            
            account_age = datetime.utcnow() - member.created_at
            age_days = account_age.days
            
            # Verdächtigkeits-Score
            suspicious_factors = []
            if age_days < 1:
                suspicious_factors.append("Sehr neues Konto (< 1 Tag)")
            elif age_days < 7:
                suspicious_factors.append("Neues Konto (< 7 Tage)")
            
            if member.display_avatar.is_default():
                suspicious_factors.append("Standard Avatar")
            
            # Default Username Pattern
            if len(member.name) > 10 and member.discriminator != "0":
                if member.name.lower().startswith(("discord", "user", "member")):
                    suspicious_factors.append("Verdächtiger Username")

            # Farbe basierend auf Verdächtigkeits-Level
            if member.bot:
                color = discord.Color.purple()
            elif len(suspicious_factors) >= 2:
                color = discord.Color.red()
            elif suspicious_factors:
                color = discord.Color.orange()
            else:
                color = discord.Color.green()

            extra_fields = {
                "🎂 Konto-Alter": f"{age_days} Tag{'e' if age_days != 1 else ''}",
                "👥 Member #": f"{member.guild.member_count}",
            }

            if suspicious_factors:
                extra_fields["⚠️ Verdächtig"] = "\n".join(suspicious_factors[:3])

            if member.bot:
                extra_fields["🤖 Bot"] = "✅"

            embed = self._create_user_embed(
                "📥 Member beigetreten", 
                member, 
                color, 
                extra_fields
            )

            await self.send_log(member.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_member_join: {e}")
            self._stats['errors'] += 1

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Verbessertes Member Leave Logging"""
        try:
            self._stats['events_processed'] += 1
            
            extra_fields = {
                "🎭 Rollen": f"{len(member.roles) - 1}",  # -1 für @everyone
                "👥 Member #": f"{member.guild.member_count}",
            }

            if member.joined_at:
                duration = datetime.utcnow() - member.joined_at
                days = duration.days
                hours = duration.seconds // 3600
                
                if days > 0:
                    duration_str = f"{days} Tag{'e' if days != 1 else ''}"
                elif hours > 0:
                    duration_str = f"{hours} Stunde{'n' if hours != 1 else ''}"
                else:
                    minutes = duration.seconds // 60
                    duration_str = f"{minutes} Minute{'n' if minutes != 1 else ''}"
                
                extra_fields["⏱️ Mitgliedschaftsdauer"] = duration_str

            # Top Rollen anzeigen (nicht @everyone)
            top_roles = [role for role in member.roles if role.name != "@everyone"]
            if top_roles:
                top_roles = sorted(top_roles, key=lambda r: r.position, reverse=True)[:3]
                extra_fields["🏆 Top Rollen"] = ", ".join([role.name for role in top_roles])

            embed = self._create_user_embed(
                "📤 Member verlassen", 
                member, 
                discord.Color.red(), 
                extra_fields
            )

            await self.send_log(member.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_member_remove: {e}")
            self._stats['errors'] += 1

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Stark verbessertes Message Delete Logging mit Bulk-Detection"""
        try:
            if message.author.bot or not message.guild:
                return

            self._stats['events_processed'] += 1
            guild_id = message.guild.id

            # Bulk Delete Detection
            current_time = datetime.utcnow()
            
            if guild_id not in self._bulk_deletes:
                self._bulk_deletes[guild_id] = {
                    'messages': set(),
                    'timestamp': current_time,
                    'channels': set()
                }

            bulk_data = self._bulk_deletes[guild_id]
            
            # Reset wenn zu alt
            if (current_time - bulk_data['timestamp']).total_seconds() > self.config['bulk_delete_window']:
                bulk_data['messages'].clear()
                bulk_data['channels'].clear()
                bulk_data['timestamp'] = current_time

            bulk_data['messages'].add(message.id)
            bulk_data['channels'].add(message.channel.id)

            # Kurz warten um weitere Deletes zu erfassen
            await asyncio.sleep(0.3)

            # Bulk Delete Check
            if len(bulk_data['messages']) >= self.config['bulk_delete_threshold']:
                embed = discord.Embed(
                    title="🗑️ Bulk-Löschung erkannt",
                    description=f"**{len(bulk_data['messages'])}** Nachrichten wurden in kurzer Zeit gelöscht",
                    color=discord.Color.dark_red(),
                    timestamp=datetime.utcnow()
                )
                
                # Channel Info
                affected_channels = []
                for ch_id in bulk_data['channels']:
                    channel = self.bot.get_channel(ch_id)
                    if channel:
                        affected_channels.append(channel.mention)
                
                if affected_channels:
                    embed.add_field(
                        name="📍 Betroffene Channels", 
                        value="\n".join(affected_channels[:5]), 
                        inline=False
                    )

                embed.add_field(name="⏱️ Zeitfenster", value=f"< {self.config['bulk_delete_window']}s", inline=True)
                embed.add_field(name="🔍 Hinweis", value="Mögliche Moderator-Aktion oder Bot-Cleanup", inline=True)

                await self.send_log(guild_id, embed, "messages")
                
                # Cache zurücksetzen
                bulk_data['messages'].clear()
                bulk_data['channels'].clear()
                return

            # Normale Delete-Behandlung
            if message.id not in bulk_data['messages']:
                return  # Bereits als Bulk verarbeitet

            embed = discord.Embed(
                title="🗑️ Nachricht gelöscht",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            # Author Info
            embed.add_field(
                name="👤 Author", 
                value=f"{message.author.mention}\n`{message.author}`", 
                inline=True
            )
            embed.add_field(
                name="📍 Channel", 
                value=message.channel.mention, 
                inline=True
            )
            embed.add_field(
                name="⏰ Erstellt", 
                value=f"<t:{int(message.created_at.timestamp())}:R>", 
                inline=True
            )

            # Content
            if message.content:
                embed.add_field(
                    name="💬 Inhalt", 
                    value=self._format_content_for_embed(message.content), 
                    inline=False
                )

            # Attachments
            if message.attachments:
                attachment_info = []
                for att in message.attachments[:self.config['max_attachment_display']]:
                    size_kb = att.size // 1024
                    attachment_info.append(f"📎 `{att.filename}` ({size_kb} KB)")
                
                if len(message.attachments) > self.config['max_attachment_display']:
                    attachment_info.append(f"... und {len(message.attachments) - self.config['max_attachment_display']} weitere")
                
                embed.add_field(
                    name="📎 Anhänge", 
                    value="\n".join(attachment_info), 
                    inline=False
                )

            # Embeds
            if message.embeds:
                embed.add_field(
                    name="📋 Embeds", 
                    value=f"{len(message.embeds)} Embed(s)", 
                    inline=True
                )

            # Reactions
            if message.reactions:
                reaction_count = sum(r.count for r in message.reactions)
                embed.add_field(
                    name="👍 Reaktionen", 
                    value=f"{reaction_count} Reaktionen", 
                    inline=True
                )

            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"Message ID: {message.id} | User ID: {message.author.id}")

            await self.send_log(guild_id, embed, "messages")
            
            # Message aus bulk cache entfernen
            if message.id in bulk_data['messages']:
                bulk_data['messages'].discard(message.id)

        except Exception as e:
            logger.error(f"Error in on_message_delete: {e}")
            self._stats['errors'] += 1

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Verbessertes Message Edit Logging mit intelligentem Debouncing"""
        try:
            if (before.author.bot or not before.guild or 
                before.content == after.content or not before.content):
                return

            self._stats['events_processed'] += 1
            message_id = before.id

            # Bestehenden Task canceln
            if message_id in self._edit_tasks:
                self._edit_tasks[message_id].cancel()

            # Neuen debounced Task erstellen
            self._edit_tasks[message_id] = asyncio.create_task(
                self._delayed_edit_log(before, after)
            )

        except Exception as e:
            logger.error(f"Error in on_message_edit: {e}")
            self._stats['errors'] += 1

    async def _delayed_edit_log(self, before: discord.Message, after: discord.Message):
        """Verzögertes Edit-Logging mit verbesserter Logik"""
        try:
            await asyncio.sleep(self.config['edit_debounce_time'])
            
            # Aktuellste Version der Nachricht holen
            try:
                fresh_message = await before.channel.fetch_message(before.id)
                after = fresh_message  # Aktuellste Version verwenden
            except (discord.NotFound, discord.Forbidden):
                pass  # Nachricht wurde gelöscht oder keine Berechtigung

            await self._log_message_edit(before, after)
            
        except asyncio.CancelledError:
            pass  # Task wurde gecancelt
        except Exception as e:
            logger.error(f"Error in delayed edit log: {e}")
        finally:
            # Task aus Cache entfernen
            if before.id in self._edit_tasks:
                del self._edit_tasks[before.id]

    async def _log_message_edit(self, before: discord.Message, after: discord.Message):
        """Internes Message Edit Logging mit Diff-Anzeige"""
        try:
            embed = discord.Embed(
                title="✏️ Nachricht bearbeitet",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="👤 Author", 
                value=f"{before.author.mention}\n`{before.author}`", 
                inline=True
            )
            embed.add_field(
                name="📍 Channel", 
                value=before.channel.mention, 
                inline=True
            )
            embed.add_field(
                name="🔗 Nachricht", 
                value=f"[Zur Nachricht]({after.jump_url})", 
                inline=True
            )

            # Content Comparison - intelligenter
            before_content = self._truncate_content(before.content or "", 700)
            after_content = self._truncate_content(after.content or "", 700)

            if len(before_content) + len(after_content) < 2000:
                embed.add_field(
                    name="📝 Vorher", 
                    value=self._format_content_for_embed(before_content, escape_markdown=True), 
                    inline=False
                )
                embed.add_field(
                    name="📝 Nachher", 
                    value=self._format_content_for_embed(after_content, escape_markdown=True), 
                    inline=False
                )
            else:
                # Zu lang - nur Änderungsinfo
                char_diff = len(after.content) - len(before.content)
                diff_text = f"**Zeichen-Änderung:** {char_diff:+d}\n"
                diff_text += f"**Länge:** {len(before.content)} → {len(after.content)}"
                
                embed.add_field(
                    name="📊 Änderungsinfo", 
                    value=diff_text, 
                    inline=False
                )

            # Timestamp der ursprünglichen Nachricht
            embed.add_field(
                name="🕐 Original erstellt", 
                value=f"<t:{int(before.created_at.timestamp())}:R>", 
                inline=True
            )

            embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
            embed.set_footer(text=f"Message ID: {before.id} | User ID: {before.author.id}")

            await self.send_log(before.guild.id, embed, "messages")

        except Exception as e:
            logger.error(f"Error in _log_message_edit: {e}")

# =============================================================================
    # VOICE STATE EVENTS
    # =============================================================================

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Verbessertes Voice State Logging mit intelligenter Filterung"""
        try:
            if member.bot:
                return

            self._stats['events_processed'] += 1
            guild_id = member.guild.id

            # Cache initialisieren
            if guild_id not in self._voice_cache:
                self._voice_cache[guild_id] = {}
            
            guild_cache = self._voice_cache[guild_id]
            member_id = member.id

            # Vorherigen State aus Cache holen oder setzen
            cached_before = guild_cache.get(member_id)
            guild_cache[member_id] = after

            # Event-Typ bestimmen
            event_type = None
            color = discord.Color.blue()
            title = ""
            
            if not before.channel and after.channel:
                # Join
                event_type = "join"
                title = "🔊 Voice Channel beigetreten"
                color = discord.Color.green()
            elif before.channel and not after.channel:
                # Leave
                event_type = "leave"
                title = "🔇 Voice Channel verlassen"
                color = discord.Color.red()
            elif before.channel != after.channel and before.channel and after.channel:
                # Move
                event_type = "move"
                title = "🔄 Voice Channel gewechselt"
                color = discord.Color.orange()
            elif before.channel == after.channel:
                # State changes (mute, deafen, etc.)
                changes = []
                if before.self_mute != after.self_mute:
                    changes.append(f"Self Mute: {'✅' if after.self_mute else '❌'}")
                if before.self_deaf != after.self_deaf:
                    changes.append(f"Self Deaf: {'✅' if after.self_deaf else '❌'}")
                if before.mute != after.mute:
                    changes.append(f"Server Mute: {'✅' if after.mute else '❌'}")
                if before.deaf != after.deaf:
                    changes.append(f"Server Deaf: {'✅' if after.deaf else '❌'}")
                if before.streaming != after.streaming:
                    changes.append(f"Streaming: {'✅' if after.streaming else '❌'}")
                if before.self_video != after.self_video:
                    changes.append(f"Camera: {'✅' if after.self_video else '❌'}")

                if changes:
                    event_type = "state_change"
                    title = "🎛️ Voice Status geändert"
                    color = discord.Color.blue()

            if not event_type:
                return

            embed = discord.Embed(
                title=title,
                color=color,
                timestamp=datetime.utcnow()
            )

            # User Info
            embed.add_field(
                name="👤 User", 
                value=f"{member.mention}\n`{member}`", 
                inline=True
            )

            # Channel Info
            if event_type == "join":
                embed.add_field(
                    name="📍 Channel", 
                    value=after.channel.mention, 
                    inline=True
                )
                # Wer ist noch im Channel?
                other_members = [m for m in after.channel.members if m != member and not m.bot]
                if other_members:
                    embed.add_field(
                        name="👥 Andere Mitglieder", 
                        value=f"{len(other_members)} Mitglied{'er' if len(other_members) != 1 else ''}", 
                        inline=True
                    )

            elif event_type == "leave":
                embed.add_field(
                    name="📍 Channel", 
                    value=before.channel.mention, 
                    inline=True
                )
                # Session-Dauer berechnen wenn im Cache
                if cached_before and cached_before.channel:
                    # Schätze Join-Zeit (grober Wert)
                    embed.add_field(
                        name="⏱️ Ungefähre Dauer", 
                        value="Session beendet", 
                        inline=True
                    )

            elif event_type == "move":
                embed.add_field(
                    name="📍 Von", 
                    value=before.channel.mention, 
                    inline=True
                )
                embed.add_field(
                    name="📍 Nach", 
                    value=after.channel.mention, 
                    inline=True
                )

            elif event_type == "state_change":
                embed.add_field(
                    name="📍 Channel", 
                    value=after.channel.mention, 
                    inline=True
                )
                embed.add_field(
                    name="🔧 Änderungen", 
                    value="\n".join(changes), 
                    inline=False
                )

            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")

            await self.send_log(guild_id, embed, "voice")

        except Exception as e:
            logger.error(f"Error in on_voice_state_update: {e}")
            self._stats['errors'] += 1

    # =============================================================================
    # MEMBER UPDATE EVENTS
    # =============================================================================

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Member Update Logging mit intelligenter Filterung"""
        try:
            if before.bot:
                return

            self._stats['events_processed'] += 1
            changes = []
            important_change = False

            # Nickname Änderung
            if before.display_name != after.display_name:
                changes.append({
                    'field': '🏷️ Nickname',
                    'before': before.display_name or "*Kein Nickname*",
                    'after': after.display_name or "*Kein Nickname*"
                })
                important_change = True

            # Rollen Änderung
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles

            if added_roles or removed_roles:
                important_change = True
                
                if added_roles:
                    role_names = [role.name for role in added_roles if role.name != "@everyone"]
                    if role_names:
                        changes.append({
                            'field': '➕ Rollen hinzugefügt',
                            'value': ", ".join(role_names[:5])  # Max 5 anzeigen
                        })

                if removed_roles:
                    role_names = [role.name for role in removed_roles if role.name != "@everyone"]
                    if role_names:
                        changes.append({
                            'field': '➖ Rollen entfernt',
                            'value': ", ".join(role_names[:5])  # Max 5 anzeigen
                        })

            # Premium Status (Nitro Boost)
            if hasattr(before, 'premium_since') and hasattr(after, 'premium_since'):
                if before.premium_since != after.premium_since:
                    if after.premium_since and not before.premium_since:
                        changes.append({
                            'field': '💎 Server Boost',
                            'value': 'Begonnen zu boosten'
                        })
                        important_change = True
                    elif before.premium_since and not after.premium_since:
                        changes.append({
                            'field': '💎 Server Boost',
                            'value': 'Boost beendet'
                        })
                        important_change = True

            # Timeout Status
            if hasattr(before, 'timed_out_until') and hasattr(after, 'timed_out_until'):
                if before.timed_out_until != after.timed_out_until:
                    if after.timed_out_until:
                        changes.append({
                            'field': '⏸️ Timeout',
                            'value': f"Bis <t:{int(after.timed_out_until.timestamp())}:R>"
                        })
                        important_change = True
                    elif before.timed_out_until:
                        changes.append({
                            'field': '⏸️ Timeout',
                            'value': 'Timeout aufgehoben'
                        })
                        important_change = True

            # Nur loggen wenn wichtige Änderungen
            if not important_change or not changes:
                return

            embed = discord.Embed(
                title="👤 Member geändert",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="👤 Member", 
                value=f"{after.mention}\n`{after}`", 
                inline=True
            )

            # Änderungen hinzufügen
            for change in changes[:self.config['max_embed_fields'] - 2]:  # Platz für User und ID
                if 'before' in change and 'after' in change:
                    value = f"**Vorher:** {change['before']}\n**Nachher:** {change['after']}"
                else:
                    value = change['value']
                
                embed.add_field(
                    name=change['field'],
                    value=value[:1024],  # Discord limit
                    inline=False
                )

            embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)
            embed.set_footer(text=f"User ID: {after.id}")

            await self.send_log(after.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_member_update: {e}")
            self._stats['errors'] += 1

    # =============================================================================
    # CHANNEL EVENTS
    # =============================================================================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Channel Creation Logging"""
        try:
            self._stats['events_processed'] += 1

            embed = discord.Embed(
                title="➕ Channel erstellt",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            # Channel-Typ Icon
            type_icons = {
                discord.ChannelType.text: "💬",
                discord.ChannelType.voice: "🔊",
                discord.ChannelType.category: "📁",
                discord.ChannelType.news: "📢",
                discord.ChannelType.stage_voice: "🎭",
                discord.ChannelType.forum: "💭",
                discord.ChannelType.private_thread: "🧵",
                discord.ChannelType.public_thread: "🧵"
            }

            icon = type_icons.get(channel.type, "📍")
            embed.add_field(
                name="📍 Channel",
                value=f"{icon} {channel.mention}\n`{channel.name}`",
                inline=True
            )

            embed.add_field(
                name="📋 Typ",
                value=channel.type.name.replace('_', ' ').title(),
                inline=True
            )

            embed.add_field(
                name="🆔 ID",
                value=f"`{channel.id}`",
                inline=True
            )

            # Kategorie info
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📁 Kategorie",
                    value=channel.category.name,
                    inline=True
                )

            # Position
            if hasattr(channel, 'position'):
                embed.add_field(
                    name="📊 Position",
                    value=str(channel.position),
                    inline=True
                )

            embed.set_footer(text=f"Channel ID: {channel.id}")
            await self.send_log(channel.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_guild_channel_create: {e}")
            self._stats['errors'] += 1

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Channel Deletion Logging"""
        try:
            self._stats['events_processed'] += 1

            embed = discord.Embed(
                title="➖ Channel gelöscht",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            # Channel-Typ Icon
            type_icons = {
                discord.ChannelType.text: "💬",
                discord.ChannelType.voice: "🔊",
                discord.ChannelType.category: "📁",
                discord.ChannelType.news: "📢",
                discord.ChannelType.stage_voice: "🎭",
                discord.ChannelType.forum: "💭"
            }

            icon = type_icons.get(channel.type, "📍")
            embed.add_field(
                name="📍 Channel",
                value=f"{icon} `#{channel.name}`",
                inline=True
            )

            embed.add_field(
                name="📋 Typ",
                value=channel.type.name.replace('_', ' ').title(),
                inline=True
            )

            embed.add_field(
                name="🆔 ID",
                value=f"`{channel.id}`",
                inline=True
            )

            # Kategorie info
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📁 Kategorie",
                    value=channel.category.name,
                    inline=True
                )

            embed.set_footer(text=f"Channel ID: {channel.id}")
            await self.send_log(channel.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_guild_channel_delete: {e}")
            self._stats['errors'] += 1

    # =============================================================================
    # BAN/KICK EVENTS
    # =============================================================================

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Member Ban Logging"""
        try:
            self._stats['events_processed'] += 1

            # Versuche Ban-Info mit Grund zu holen
            ban_info = None
            try:
                ban_info = await guild.fetch_ban(user)
            except:
                pass

            embed = discord.Embed(
                title="🔨 Member gebannt",
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="👤 User",
                value=f"{user.mention}\n`{user}`",
                inline=True
            )

            embed.add_field(
                name="🆔 ID",
                value=f"`{user.id}`",
                inline=True
            )

            embed.add_field(
                name="📅 Account erstellt",
                value=f"<t:{int(user.created_at.timestamp())}:R>",
                inline=True
            )

            if ban_info and ban_info.reason:
                embed.add_field(
                    name="📝 Grund",
                    value=ban_info.reason[:1000],
                    inline=False
                )

            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_footer(text=f"User ID: {user.id}")

            await self.send_log(guild.id, embed, "moderation")

        except Exception as e:
            logger.error(f"Error in on_member_ban: {e}")
            self._stats['errors'] += 1

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Member Unban Logging"""
        try:
            self._stats['events_processed'] += 1

            embed = discord.Embed(
                title="🔓 Member entbannt",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="👤 User",
                value=f"{user.mention}\n`{user}`",
                inline=True
            )

            embed.add_field(
                name="🆔 ID",
                value=f"`{user.id}`",
                inline=True
            )

            embed.add_field(
                name="📅 Account erstellt",
                value=f"<t:{int(user.created_at.timestamp())}:R>",
                inline=True
            )

            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_footer(text=f"User ID: {user.id}")

            await self.send_log(guild.id, embed, "moderation")

        except Exception as e:
            logger.error(f"Error in on_member_unban: {e}")
            self._stats['errors'] += 1

    # =============================================================================
    # INVITE EVENTS
    # =============================================================================

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Invite Creation Logging"""
        try:
            self._stats['events_processed'] += 1

            embed = discord.Embed(
                title="🔗 Invite erstellt",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="🔗 Invite Code",
                value=f"`{invite.code}`",
                inline=True
            )

            embed.add_field(
                name="📍 Channel",
                value=invite.channel.mention if invite.channel else "Unbekannt",
                inline=True
            )

            if invite.inviter:
                embed.add_field(
                    name="👤 Ersteller",
                    value=f"{invite.inviter.mention}\n`{invite.inviter}`",
                    inline=True
                )

            # Invite Settings
            settings = []
            if invite.max_uses:
                settings.append(f"Max. Nutzungen: {invite.max_uses}")
            else:
                settings.append("Max. Nutzungen: ∞")

            if invite.max_age:
                settings.append(f"Ablauf: <t:{int((datetime.utcnow() + timedelta(seconds=invite.max_age)).timestamp())}:R>")
            else:
                settings.append("Ablauf: Nie")

            if invite.temporary:
                settings.append("Temporär: Ja")

            if settings:
                embed.add_field(
                    name="⚙️ Einstellungen",
                    value="\n".join(settings),
                    inline=False
                )

            if invite.inviter:
                embed.set_author(name=invite.inviter.display_name, icon_url=invite.inviter.display_avatar.url)

            embed.set_footer(text=f"Invite Code: {invite.code}")
            await self.send_log(invite.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_invite_create: {e}")
            self._stats['errors'] += 1

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Invite Deletion Logging"""
        try:
            self._stats['events_processed'] += 1

            embed = discord.Embed(
                title="🗑️ Invite gelöscht",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="🔗 Invite Code",
                value=f"`{invite.code}`",
                inline=True
            )

            embed.add_field(
                name="📍 Channel",
                value=invite.channel.mention if invite.channel else "Unbekannt",
                inline=True
            )

            if invite.uses is not None:
                embed.add_field(
                    name="📊 Verwendet",
                    value=f"{invite.uses} mal",
                    inline=True
                )

            embed.set_footer(text=f"Invite Code: {invite.code}")
            await self.send_log(invite.guild.id, embed, "general")

        except Exception as e:
            logger.error(f"Error in on_invite_delete: {e}")
            self._stats['errors'] += 1

def setup(bot):
    bot.add_cog(LoggingCog(bot))