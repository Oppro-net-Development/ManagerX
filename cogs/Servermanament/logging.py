# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from FastCoding import LoggingDatabase
from typing import Dict, Set, Tuple, Optional
import asyncio


class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = LoggingDatabase()

        # Cache für Message Edit Debouncing - Format: {message_id: task}
        self.edit_tasks: Dict[int, asyncio.Task] = {}
        self.edit_debounce_time = 2  # Sekunden

        # Cache für Bulk Delete Detection
        self.bulk_deletes: Dict[int, Set[int]] = {}
        self.bulk_delete_threshold = 5  # Anzahl gleichzeitiger Löschungen

        # Cache für Voice Activity
        self.voice_cache: Dict[int, Dict[int, Optional[discord.VoiceState]]] = {}

        # Cleanup Task für Caches
        self.cleanup_task = None
        # Start cleanup task after bot is ready
        self.bot.loop.create_task(self._start_cleanup_when_ready())

    async def _start_cleanup_when_ready(self):
        """Wait for bot to be ready before starting cleanup task"""
        await self.bot.wait_until_ready()
        self.cleanup_task = self.bot.loop.create_task(self._cleanup_caches())

    def cog_unload(self):
        """Cleanup beim Entladen der Cog"""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

    async def _cleanup_caches(self):
        """Regelmäßige Cache-Bereinigung"""
        while not self.bot.is_closed():
            try:
                # Edit Tasks bereinigen
                completed_tasks = [
                    msg_id for msg_id, task in self.edit_tasks.items()
                    if task.done()
                ]
                for msg_id in completed_tasks:
                    del self.edit_tasks[msg_id]

                # Bulk Delete Cache bereinigen (älter als 1 Minute)
                current_time = datetime.utcnow()
                for guild_id in list(self.bulk_deletes.keys()):
                    # Einfache Bereinigung nach Zeit
                    if len(self.bulk_deletes[guild_id]) == 0:
                        del self.bulk_deletes[guild_id]

                await asyncio.sleep(60)  # Alle 60 Sekunden
            except Exception as e:
                print(f"Fehler beim Cache-Cleanup: {e}")
                await asyncio.sleep(60)

    async def send_log(self, guild_id: int, embed: discord.Embed, log_type: str = "general"):
        """Sendet ein Log-Embed in den konfigurierten Channel"""
        try:
            channel_id = await self.db.get_log_channel(guild_id, log_type)
            if not channel_id:
                return False

            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False

            await channel.send(embed=embed)
            return True

        except discord.Forbidden:
            print(f"Keine Berechtigung für Log-Channel in Guild {guild_id}")
            await self.db.remove_log_channel(guild_id, log_type)
        except discord.NotFound:
            print(f"Log-Channel nicht gefunden in Guild {guild_id}")
            await self.db.remove_log_channel(guild_id, log_type)
        except Exception as e:
            print(f"Fehler beim Senden des Logs: {e}")

        return False

    def _create_user_embed(self, title: str, user: discord.User, color: discord.Color,
                           extra_fields: Dict[str, str] = None) -> discord.Embed:
        """Erstellt ein standardisiertes User-Embed"""
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=False)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.add_field(name="Konto erstellt",
                        value=f"<t:{int(user.created_at.timestamp())}:F>", inline=True)

        if extra_fields:
            for name, value in extra_fields.items():
                embed.add_field(name=name, value=str(value), inline=True)

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")

        return embed

    # Slash Commands
    @discord.slash_command(name="setlogchannel", description="Setzt den Log-Channel für verschiedene Events")
    @discord.default_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel,
                              log_type: discord.Option(str, choices=["general", "moderation", "voice", "messages"],
                                                       description="Art der Logs", default="general")):
        try:
            await self.db.set_log_channel(ctx.guild.id, channel.id, log_type)

            embed = discord.Embed(
                title="✅ Log-Channel gesetzt",
                description=f"{log_type.title()}-Logs werden nun in {channel.mention} gesendet.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Setzen des Log-Channels: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="removelogchannel", description="Entfernt einen Log-Channel")
    @discord.default_permissions(administrator=True)
    async def remove_log_channel(self, ctx,
                                 log_type: discord.Option(str,
                                                          choices=["general", "moderation", "voice", "messages", "all"],
                                                          description="Art der Logs", default="all")):
        try:
            if log_type == "all":
                await self.db.remove_all_log_channels(ctx.guild.id)
                description = "Alle Log-Channels wurden entfernt."
            else:
                await self.db.remove_log_channel(ctx.guild.id, log_type)
                description = f"{log_type.title()}-Logging wurde deaktiviert."

            embed = discord.Embed(
                title="🗑️ Log-Channel entfernt",
                description=description,
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Entfernen des Log-Channels: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="logstatus", description="Zeigt die aktuellen Log-Einstellungen")
    @discord.default_permissions(administrator=True)
    async def log_status(self, ctx):
        try:
            channels = await self.db.get_all_log_channels(ctx.guild.id)

            embed = discord.Embed(
                title="📊 Logging Status",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            if not channels:
                embed.description = "Keine Log-Channels konfiguriert."
            else:
                for log_type, channel_id in channels.items():
                    channel = self.bot.get_channel(channel_id)
                    channel_mention = channel.mention if channel else f"❌ Channel nicht gefunden ({channel_id})"
                    embed.add_field(name=log_type.title(), value=channel_mention, inline=True)

            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"Fehler beim Abrufen des Log-Status: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    # Member Events
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Member beitritt"""
        try:
            account_age = datetime.utcnow() - member.created_at
            age_text = f"{account_age.days} Tage alt"

            suspicious = account_age.days < 7
            color = discord.Color.orange() if suspicious else discord.Color.green()

            extra_fields = {
                "Konto-Alter": age_text,
                "Member #": str(member.guild.member_count)
            }

            if suspicious:
                extra_fields["⚠️ Warnung"] = "Neues Konto"

            embed = self._create_user_embed("📥 Member beigetreten", member, color, extra_fields)
            await self.send_log(member.guild.id, embed, "general")
        except Exception as e:
            print(f"Fehler in on_member_join: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Member verlässt Server"""
        try:
            join_duration = ""
            if member.joined_at:
                duration = datetime.utcnow() - member.joined_at
                join_duration = f"{duration.days} Tage Mitglied"

            extra_fields = {
                "Rollen": f"{len(member.roles) - 1}",
                "Member #": str(member.guild.member_count)
            }

            if join_duration:
                extra_fields["Mitgliedschaftsdauer"] = join_duration

            embed = self._create_user_embed("📤 Member verlassen", member, discord.Color.red(), extra_fields)
            await self.send_log(member.guild.id, embed, "general")
        except Exception as e:
            print(f"Fehler in on_member_remove: {e}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Member wurde gebannt"""
        try:
            extra_fields = {}

            try:
                ban_info = await guild.fetch_ban(user)
                if ban_info.reason:
                    extra_fields["Grund"] = ban_info.reason
            except:
                pass

            embed = self._create_user_embed("🔨 Member gebannt", user, discord.Color.dark_red(), extra_fields)
            await self.send_log(guild.id, embed, "moderation")
        except Exception as e:
            print(f"Fehler in on_member_ban: {e}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Member wurde entbannt"""
        try:
            embed = self._create_user_embed("🔓 Member entbannt", user, discord.Color.orange())
            await self.send_log(guild.id, embed, "moderation")
        except Exception as e:
            print(f"Fehler in on_member_unban: {e}")

    # Message Events
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Nachricht gelöscht"""
        try:
            if message.author.bot or not message.guild:
                return

            guild_id = message.guild.id
            if guild_id not in self.bulk_deletes:
                self.bulk_deletes[guild_id] = set()

            self.bulk_deletes[guild_id].add(message.id)

            # Kurz warten um bulk deletes zu erkennen
            await asyncio.sleep(0.5)

            # Prüfen ob es sich um bulk delete handelt
            if len(self.bulk_deletes[guild_id]) >= self.bulk_delete_threshold:
                embed = discord.Embed(
                    title="🗑️ Bulk-Löschung erkannt",
                    description=f"{len(self.bulk_deletes[guild_id])} Nachrichten wurden gleichzeitig gelöscht.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                await self.send_log(guild_id, embed, "messages")
                self.bulk_deletes[guild_id].clear()
                return

            embed = discord.Embed(
                title="🗑️ Nachricht gelöscht",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(name="Author", value=f"{message.author.mention} ({message.author})", inline=False)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            embed.add_field(name="Erstellt", value=f"<t:{int(message.created_at.timestamp())}:R>", inline=True)

            if message.content:
                content = message.content[:1000] if len(message.content) > 1000 else message.content
                # Escape markdown/code blocks in content
                content = content.replace("```", "'''")
                embed.add_field(name="Inhalt", value=f"```{content}```", inline=False)

            if message.attachments:
                attach_list = "\n".join([f"📎 {att.filename}" for att in message.attachments[:5]])
                if len(message.attachments) > 5:
                    attach_list += f"\n... und {len(message.attachments) - 5} weitere"
                embed.add_field(name="Anhänge", value=attach_list, inline=False)

            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"Message ID: {message.id} | User ID: {message.author.id}")

            await self.send_log(guild_id, embed, "messages")

            # Message aus bulk delete cache entfernen
            if message.id in self.bulk_deletes[guild_id]:
                self.bulk_deletes[guild_id].remove(message.id)
        except Exception as e:
            print(f"Fehler in on_message_delete: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Nachricht bearbeitet - mit Debouncing"""
        try:
            if before.author.bot or not before.guild or before.content == after.content:
                return

            message_id = before.id

            # Wenn bereits ein Task läuft, canceln
            if message_id in self.edit_tasks:
                self.edit_tasks[message_id].cancel()

            # Neuen Task erstellen
            self.edit_tasks[message_id] = asyncio.create_task(
                self._delayed_edit_log(before, after, self.edit_debounce_time)
            )
        except Exception as e:
            print(f"Fehler in on_message_edit: {e}")

    async def _delayed_edit_log(self, before: discord.Message, after: discord.Message, delay: float):
        """Verzögertes Edit-Logging"""
        try:
            await asyncio.sleep(delay)
            await self._log_message_edit(before, after)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Fehler beim Edit-Logging: {e}")
        finally:
            if before.id in self.edit_tasks:
                del self.edit_tasks[before.id]

    async def _log_message_edit(self, before: discord.Message, after: discord.Message):
        """Internes Message Edit Logging"""
        try:
            embed = discord.Embed(
                title="✏️ Nachricht bearbeitet",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(name="Author", value=f"{before.author.mention} ({before.author})", inline=False)
            embed.add_field(name="Channel", value=before.channel.mention, inline=True)
            embed.add_field(name="Zur Nachricht", value=f"[🔗 Springe zur Nachricht]({after.jump_url})", inline=True)

            if before.content and after.content:
                if len(before.content) <= 500 and len(after.content) <= 500:
                    # Escape markdown/code blocks
                    before_content = before.content.replace("```", "'''")
                    after_content = after.content.replace("```", "'''")
                    embed.add_field(name="⬅️ Vorher", value=f"```{before_content}```", inline=False)
                    embed.add_field(name="➡️ Nachher", value=f"```{after_content}```", inline=False)
                else:
                    embed.add_field(name="📝 Änderung", value="Nachricht wurde bearbeitet (zu lang für Anzeige)",
                                    inline=False)

            embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
            embed.set_footer(text=f"Message ID: {before.id} | User ID: {before.author.id}")

            await self.send_log(before.guild.id, embed, "messages")
        except Exception as e:
            print(f"Fehler in _log_message_edit: {e}")

    # Voice Events
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """Voice State Updates"""
        try:
            guild_id = member.guild.id

            if guild_id not in self.voice_cache:
                self.voice_cache[guild_id] = {}

            self.voice_cache[guild_id][member.id] = after

            embed = None

            # Join
            if not before.channel and after.channel:
                embed = discord.Embed(
                    title="🔊 Voice Channel beigetreten",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Channel", value=after.channel.mention, inline=True)

            # Leave
            elif before.channel and not after.channel:
                embed = discord.Embed(
                    title="🔇 Voice Channel verlassen",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Channel", value=before.channel.mention, inline=True)

            # Switch
            elif before.channel and after.channel and before.channel != after.channel:
                embed = discord.Embed(
                    title="🔄 Voice Channel gewechselt",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Von", value=before.channel.mention, inline=True)
                embed.add_field(name="Nach", value=after.channel.mention, inline=True)

            # Status Changes
            elif before.channel == after.channel and after.channel:
                changes = []
                if before.mute != after.mute:
                    changes.append(f"Mute: {before.mute} → {after.mute}")
                if before.deaf != after.deaf:
                    changes.append(f"Deaf: {before.deaf} → {after.deaf}")
                if before.self_mute != after.self_mute:
                    changes.append(f"Self-Mute: {before.self_mute} → {after.self_mute}")
                if before.self_deaf != after.self_deaf:
                    changes.append(f"Self-Deaf: {before.self_deaf} → {after.self_deaf}")

                if changes:
                    embed = discord.Embed(
                        title="🎙️ Voice Status geändert",
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Channel", value=after.channel.mention, inline=True)
                    embed.add_field(name="Änderungen", value="\n".join(changes), inline=False)

            if embed:
                embed.add_field(name="User", value=f"{member.mention} ({member})", inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"User ID: {member.id}")
                await self.send_log(guild_id, embed, "voice")
        except Exception as e:
            print(f"Fehler in on_voice_state_update: {e}")

    # Server Events
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Channel erstellt"""
        try:
            embed = discord.Embed(
                title="📁 Channel erstellt",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Channel", value=f"{channel.mention} ({channel.name})", inline=False)
            embed.add_field(name="Typ", value=str(channel.type).replace('_', ' ').title(), inline=True)
            embed.add_field(name="Position", value=str(channel.position), inline=True)
            embed.add_field(name="ID", value=str(channel.id), inline=True)

            if hasattr(channel, 'category') and channel.category:
                embed.add_field(name="Kategorie", value=channel.category.name, inline=True)

            await self.send_log(channel.guild.id, embed, "general")
        except Exception as e:
            print(f"Fehler in on_guild_channel_create: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Channel gelöscht"""
        try:
            embed = discord.Embed(
                title="🗑️ Channel gelöscht",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Channel", value=f"#{channel.name}", inline=False)
            embed.add_field(name="Typ", value=str(channel.type).replace('_', ' ').title(), inline=True)
            embed.add_field(name="ID", value=str(channel.id), inline=True)

            if hasattr(channel, 'category') and channel.category:
                embed.add_field(name="Kategorie", value=channel.category.name, inline=True)

            await self.send_log(channel.guild.id, embed, "general")
        except Exception as e:
            print(f"Fehler in on_guild_channel_delete: {e}")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Rolle erstellt"""
        try:
            embed = discord.Embed(
                title="🎭 Rolle erstellt",
                color=role.color if role.color != discord.Color.default() else discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Rolle", value=f"{role.mention} ({role.name})", inline=False)
            embed.add_field(name="Farbe", value=str(role.color), inline=True)
            embed.add_field(name="Position", value=str(role.position), inline=True)
            embed.add_field(name="Mentionable", value="✅" if role.mentionable else "❌", inline=True)
            embed.add_field(name="Getrennt anzeigen", value="✅" if role.hoist else "❌", inline=True)
            embed.add_field(name="ID", value=str(role.id), inline=True)

            await self.send_log(role.guild.id, embed, "general")
        except Exception as e:
            print(f"Fehler in on_guild_role_create: {e}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Rolle gelöscht"""
        try:
            embed = discord.Embed(
                title="🗑️ Rolle gelöscht",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Rolle", value=role.name, inline=False)
            embed.add_field(name="Farbe", value=str(role.color), inline=True)
            embed.add_field(name="Position", value=str(role.position), inline=True)
            embed.add_field(name="Mitglieder", value=str(len(role.members)), inline=True)
            embed.add_field(name="ID", value=str(role.id), inline=True)

            await self.send_log(role.guild.id, embed, "general")
        except Exception as e:
            print(f"Fehler in on_guild_role_delete: {e}")

    # Member Update Events
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Member Update (Nickname, Rollen, etc.)"""
        try:
            # Nickname Change
            if before.nick != after.nick:
                embed = discord.Embed(
                    title="📝 Nickname geändert",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)
                embed.add_field(name="Vorher", value=before.nick or "*(Kein Nickname)*", inline=True)
                embed.add_field(name="Nachher", value=after.nick or "*(Kein Nickname)*", inline=True)
                embed.set_thumbnail(url=after.display_avatar.url)
                embed.set_footer(text=f"User ID: {after.id}")

                await self.send_log(after.guild.id, embed, "general")

            # Role Changes
            if before.roles != after.roles:
                added_roles = set(after.roles) - set(before.roles)
                removed_roles = set(before.roles) - set(after.roles)

                # Rolle hinzugefügt
                if added_roles:
                    embed = discord.Embed(
                        title="➕ Rolle(n) hinzugefügt",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)

                    role_mentions = []
                    for role in sorted(added_roles, key=lambda r: r.position, reverse=True):
                        role_mentions.append(role.mention)

                    embed.add_field(name="Hinzugefügte Rollen", value=", ".join(role_mentions), inline=False)
                    embed.add_field(name="Gesamt Rollen", value=f"{len(after.roles) - 1}", inline=True)
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.set_footer(text=f"User ID: {after.id}")

                    await self.send_log(after.guild.id, embed, "general")

                # Rolle entfernt
                if removed_roles:
                    embed = discord.Embed(
                        title="➖ Rolle(n) entfernt",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)

                    role_names = []
                    for role in sorted(removed_roles, key=lambda r: r.position, reverse=True):
                        role_names.append(role.name)

                    embed.add_field(name="Entfernte Rollen", value=", ".join(role_names), inline=False)
                    embed.add_field(name="Gesamt Rollen", value=f"{len(after.roles) - 1}", inline=True)
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.set_footer(text=f"User ID: {after.id}")

                    await self.send_log(after.guild.id, embed, "general")

            # Timeout Changes
            if before.communication_disabled_until != after.communication_disabled_until:
                if after.communication_disabled_until:
                    embed = discord.Embed(
                        title="⏰ Timeout erhalten",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)
                    embed.add_field(name="Timeout bis",
                                    value=f"<t:{int(after.communication_disabled_until.timestamp())}:F>", inline=False)
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.set_footer(text=f"User ID: {after.id}")

                    await self.send_log(after.guild.id, embed, "moderation")
                else:
                    embed = discord.Embed(
                        title="✅ Timeout aufgehoben",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.set_footer(text=f"User ID: {after.id}")

                    await self.send_log(after.guild.id, embed, "moderation")
        except Exception as e:
            print(f"Fehler in on_member_update: {e}")

def setup(bot):
    bot.add_cog(LoggingCog(bot))