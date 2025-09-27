# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
from DevTools.backend import discord, ezcord, slash_command, option, timedelta, SlashCommandGroup
from DevTools.backend import KICK, BAN, MODERATE
from DevTools.ui import emoji_yes, emoji_no, emoji_user, emoji_warning, emoji_circleinfo
from DevTools.ui import ERROR_TITLE, ERROR_COLOR, SUCCESS_COLOR, AUTHOR, FLOOTER

import asyncio
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List
import logging

# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class Moderation(ezcord.Cog):
    """Erweiterte Moderations-Cog mit verbesserter Sicherheit und Fehlerbehandlung"""

    def __init__(self, bot):
        self.bot = bot
        # Maximale Timeout-Dauer (Discord Limit: 28 Tage)
        self.max_timeout_days = 28
        # Cache für aktive Abstimmungen
        self._active_votes: Dict[int, Dict] = {}
        # Logging setup
        self.logger = logging.getLogger(__name__)

    # SlashCommandGroup als Klassenattribut
    moderation = SlashCommandGroup("moderation", "Erweiterte Moderationsbefehle")

    def _has_permission(self, member: discord.Member, permission: str) -> bool:
        """Überprüft ob ein Member eine bestimmte Berechtigung hat"""
        return getattr(member.guild_permissions, permission, False)

    def _can_moderate_member(self, moderator: discord.Member, target: discord.Member) -> tuple[bool, str]:
        """Erweiterte Überprüfung ob ein Moderator ein Ziel-Mitglied moderieren kann"""

        # Bot-Owner kann nicht moderiert werden
        if target.id == target.guild.owner_id:
            return False, "Der Server-Owner kann nicht moderiert werden."

        # Selbst-Moderation verhindern
        if moderator.id == target.id:
            return False, "Du kannst dich nicht selbst moderieren."

        # Bot kann sich nicht selbst moderieren
        if target.id == self.bot.user.id:
            return False, "Ich kann mich nicht selbst moderieren."

        # Andere Bots prüfen
        if target.bot and not moderator.guild_permissions.administrator:
            return False, "Nur Administratoren können Bots moderieren."

        # Rollen-Hierarchie prüfen (Owner ist ausgenommen)
        if moderator.id != target.guild.owner_id:
            if moderator.top_role <= target.top_role:
                return False, "Du kannst keine Mitglieder mit gleicher oder höherer Rolle moderieren."

        # Bot-Berechtigung prüfen
        bot_member = target.guild.get_member(self.bot.user.id)
        if bot_member and bot_member.top_role <= target.top_role:
            return False, "Meine Rolle ist nicht hoch genug, um dieses Mitglied zu moderieren."

        return True, ""

    def _parse_duration(self, duration_str: str) -> Optional[timedelta]:
        """Erweiterte Dauer-Parsing mit mehr Formaten und besserer Validierung"""
        # Normalisierung des Eingabestrings
        duration_str = duration_str.lower().strip()
        
        # Regex für verschiedene Formate: 1h30m, 2d, 45m, 1w2d, etc.
        pattern = r'(\d+)([smhdw])'
        matches = re.findall(pattern, duration_str)

        if not matches:
            return None

        total_seconds = 0

        for amount_str, unit in matches:
            try:
                amount = int(amount_str)
            except ValueError:
                return None

            if amount < 0:
                return None

            if unit == 's':
                total_seconds += amount
            elif unit == 'm':
                total_seconds += amount * 60
            elif unit == 'h':
                total_seconds += amount * 3600
            elif unit == 'd':
                total_seconds += amount * 86400
            elif unit == 'w':
                total_seconds += amount * 604800  # 7 Tage
            else:
                return None

        # Minimale und maximale Dauer prüfen
        if total_seconds < 1:  # Mindestens 1 Sekunde
            return None
            
        max_seconds = self.max_timeout_days * 86400
        if total_seconds > max_seconds:
            return None

        return timedelta(seconds=total_seconds)

    def _format_duration(self, duration: timedelta) -> str:
        """Formatiert eine timedelta in einen lesbaren String"""
        total_seconds = int(duration.total_seconds())
        
        weeks = total_seconds // 604800
        days = (total_seconds % 604800) // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if weeks: parts.append(f"{weeks}w")
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        if seconds: parts.append(f"{seconds}s")
        
        return " ".join(parts) if parts else "0s"

    def _create_moderation_embed(self, action: str, moderator: discord.Member, target: discord.Member,
                                reason: str, duration: str = None, additional_info: str = None) -> discord.Embed:
        """Erstellt ein einheitliches Moderations-Embed"""
        
        # Farbe basierend auf Aktion
        color_map = {
            "Bann": discord.Color.dark_red(),
            "Kick": discord.Color.red(),
            "Timeout": discord.Color.orange(),
            "Timeout aufgehoben": discord.Color.green(),
            "Slowmode aktiviert": discord.Color.blue(),
            "Slowmode deaktiviert": discord.Color.green(),
        }
        
        embed = discord.Embed(
            title=f"{emoji_yes} {action} erfolgreich",
            color=color_map.get(action, SUCCESS_COLOR),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(name=AUTHOR)

        # Basis-Felder
        if target:
            embed.add_field(name="🎯 Ziel", value=f"{target.mention} ({target})", inline=True)
        embed.add_field(name="👮 Moderator", value=moderator.mention, inline=True)

        if duration:
            embed.add_field(name="⏱️ Dauer", value=duration, inline=True)

        embed.add_field(name="📝 Grund", value=reason, inline=False)

        if additional_info:
            embed.add_field(name="ℹ️ Zusätzlich", value=additional_info, inline=False)

        if target:
            embed.set_footer(text=f"User ID: {target.id}")
        else:
            embed.set_footer(text=FLOOTER)

        return embed

    def _create_error_embed(self, title: str, description: str, additional_info: str = None) -> discord.Embed:
        """Erstellt ein einheitliches Error-Embed"""
        embed = discord.Embed(
            title=f"{emoji_no} {title}",
            description=description,
            color=ERROR_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(name=AUTHOR)
        
        if additional_info:
            embed.add_field(name="Details", value=additional_info, inline=False)
            
        embed.set_footer(text=FLOOTER)
        return embed

    # ✅ Verbesserter Ban Command
    @moderation.command(name="ban", description="Bannt ein Mitglied vom Server")
    @option("member", discord.Member, description="Das zu bannende Mitglied")
    @option("reason", str, description="Grund für den Bann", max_length=500, required=False)
    @option("delete_messages", bool, description="Nachrichten der letzten 7 Tage löschen?", required=False, default=False)
    @option("notify_user", bool, description="User per DM benachrichtigen?", required=False, default=True)
    async def ban(self, ctx: discord.ApplicationContext, member: discord.Member,
                  reason: str = "Kein Grund angegeben", delete_messages: bool = False, notify_user: bool = True):

        await ctx.defer(ephemeral=True)

        try:
            # Berechtigung prüfen
            if not self._has_permission(ctx.author, BAN):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst die `Mitglieder bannen` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Bot-Berechtigung prüfen
            if not self._has_permission(ctx.guild.me, BAN):
                embed = self._create_error_embed(
                    "Bot-Berechtigung fehlt",
                    "Mir fehlt die `Mitglieder bannen` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = self._create_error_embed("Moderation nicht möglich", error_msg)
                return await ctx.followup.send(embed=embed)

            # User benachrichtigen (vor dem Bann)
            notification_sent = False
            if notify_user:
                try:
                    dm_embed = discord.Embed(
                        title=f"{emoji_warning} Du wurdest gebannt",
                        color=ERROR_COLOR,
                        description=f"Du wurdest von **{ctx.guild.name}** gebannt."
                    )
                    dm_embed.add_field(name="Grund", value=reason, inline=False)
                    dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                    dm_embed.set_footer(text="Bei Fragen wende dich an die Serverleitung.")
                    
                    await member.send(embed=dm_embed)
                    notification_sent = True
                except discord.Forbidden:
                    pass  # DMs deaktiviert

            # Bann durchführen
            delete_days = 7 if delete_messages else 0
            ban_reason = f"{reason} | Moderator: {ctx.author} ({ctx.author.id})"
            
            await member.ban(reason=ban_reason, delete_message_days=delete_days)

            # Erfolgs-Embed
            additional_info = []
            if delete_messages:
                additional_info.append("Nachrichten der letzten 7 Tage gelöscht")
            if notification_sent:
                additional_info.append("User per DM benachrichtigt")
            elif notify_user:
                additional_info.append("DM-Benachrichtigung fehlgeschlagen")

            embed = self._create_moderation_embed(
                "Bann", ctx.author, member, reason,
                additional_info="\n".join(additional_info) if additional_info else None
            )

            await ctx.followup.send(embed=embed)
            self.logger.info(f"User {member} ({member.id}) banned by {ctx.author} ({ctx.author.id}): {reason}")

        except discord.Forbidden:
            embed = self._create_error_embed(
                "Berechtigung verweigert",
                f"Mir fehlen die Berechtigungen, um {member.mention} zu bannen.",
                "Stelle sicher, dass meine Rolle höher als die des Ziels ist."
            )
            await ctx.followup.send(embed=embed)
        except discord.HTTPException as e:
            embed = self._create_error_embed(
                "Discord-Fehler",
                f"Fehler beim Bannen: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
            self.logger.error(f"Unexpected error in ban command: {e}", exc_info=True)

    # ✅ Verbesserter Kick Command
    @moderation.command(name="kick", description="Kickt ein Mitglied vom Server")
    @option("member", discord.Member, description="Das zu kickende Mitglied")
    @option("reason", str, description="Grund für den Kick", max_length=500, required=False)
    @option("notify_user", bool, description="User per DM benachrichtigen?", required=False, default=True)
    async def kick(self, ctx: discord.ApplicationContext, member: discord.Member,
                   reason: str = "Kein Grund angegeben", notify_user: bool = True):

        await ctx.defer(ephemeral=True)

        try:
            # Berechtigung prüfen
            if not self._has_permission(ctx.author, KICK):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst die `Mitglieder kicken` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Bot-Berechtigung prüfen
            if not self._has_permission(ctx.guild.me, KICK):
                embed = self._create_error_embed(
                    "Bot-Berechtigung fehlt",
                    "Mir fehlt die `Mitglieder kicken` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = self._create_error_embed("Moderation nicht möglich", error_msg)
                return await ctx.followup.send(embed=embed)

            # User benachrichtigen (vor dem Kick)
            notification_sent = False
            if notify_user:
                try:
                    dm_embed = discord.Embed(
                        title=f"{emoji_warning} Du wurdest gekickt",
                        color=ERROR_COLOR,
                        description=f"Du wurdest von **{ctx.guild.name}** gekickt."
                    )
                    dm_embed.add_field(name="Grund", value=reason, inline=False)
                    dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                    dm_embed.set_footer(text="Du kannst dem Server erneut beitreten.")
                    
                    await member.send(embed=dm_embed)
                    notification_sent = True
                except discord.Forbidden:
                    pass  # DMs deaktiviert

            # Kick durchführen
            kick_reason = f"{reason} | Moderator: {ctx.author} ({ctx.author.id})"
            await member.kick(reason=kick_reason)

            # Erfolgs-Embed
            additional_info = None
            if notification_sent:
                additional_info = "User per DM benachrichtigt"
            elif notify_user:
                additional_info = "DM-Benachrichtigung fehlgeschlagen"

            embed = self._create_moderation_embed(
                "Kick", ctx.author, member, reason,
                additional_info=additional_info
            )

            await ctx.followup.send(embed=embed)
            self.logger.info(f"User {member} ({member.id}) kicked by {ctx.author} ({ctx.author.id}): {reason}")

        except discord.Forbidden:
            embed = self._create_error_embed(
                "Berechtigung verweigert",
                f"Mir fehlen die Berechtigungen, um {member.mention} zu kicken.",
                "Stelle sicher, dass meine Rolle höher als die des Ziels ist."
            )
            await ctx.followup.send(embed=embed)
        except discord.HTTPException as e:
            embed = self._create_error_embed(
                "Discord-Fehler",
                f"Fehler beim Kicken: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
            self.logger.error(f"Unexpected error in kick command: {e}", exc_info=True)

    # ✅ Verbesserter Timeout Command
    @moderation.command(name="timeout", description="Versetzt ein Mitglied in Timeout")
    @option("member", discord.Member, description="Das zu mutende Mitglied")
    @option("duration", str, description="Dauer (z.B. 10m, 1h30m, 2d, 1w)")
    @option("reason", str, description="Grund für den Timeout", max_length=500, required=False)
    @option("notify_user", bool, description="User per DM benachrichtigen?", required=False, default=True)
    async def timeout(self, ctx: discord.ApplicationContext, member: discord.Member,
                      duration: str, reason: str = "Kein Grund angegeben", notify_user: bool = True):

        await ctx.defer(ephemeral=True)

        try:
            # Berechtigung prüfen
            if not self._has_permission(ctx.author, MODERATE):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst die `Mitglieder moderieren` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Bot-Berechtigung prüfen
            if not self._has_permission(ctx.guild.me, MODERATE):
                embed = self._create_error_embed(
                    "Bot-Berechtigung fehlt",
                    "Mir fehlt die `Mitglieder moderieren` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = self._create_error_embed("Moderation nicht möglich", error_msg)
                return await ctx.followup.send(embed=embed)

            # Dauer parsen
            parsed_duration = self._parse_duration(duration)
            if parsed_duration is None:
                embed = self._create_error_embed(
                    "Ungültige Dauer",
                    f"Konnte '{duration}' nicht als gültige Dauer erkennen.",
                    f"Beispiele: `10m`, `1h30m`, `2d`, `1w`\nMaximum: {self.max_timeout_days} Tage"
                )
                return await ctx.followup.send(embed=embed)

            # Prüfung ob User bereits in Timeout ist
            if member.communication_disabled_until and member.communication_disabled_until > datetime.now(timezone.utc):
                current_timeout = member.communication_disabled_until
                embed = self._create_error_embed(
                    "User bereits in Timeout",
                    f"{member.mention} ist bereits bis {discord.utils.format_dt(current_timeout, 'F')} in Timeout.",
                    "Verwende `/moderation untimeout` um den aktuellen Timeout zu beenden."
                )
                return await ctx.followup.send(embed=embed)

            # User benachrichtigen (vor dem Timeout)
            notification_sent = False
            if notify_user:
                try:
                    dm_embed = discord.Embed(
                        title=f"{emoji_warning} Du wurdest in Timeout versetzt",
                        color=ERROR_COLOR,
                        description=f"Du wurdest auf **{ctx.guild.name}** in Timeout versetzt."
                    )
                    dm_embed.add_field(name="Dauer", value=self._format_duration(parsed_duration), inline=True)
                    dm_embed.add_field(name="Grund", value=reason, inline=False)
                    dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                    
                    end_time = datetime.now(timezone.utc) + parsed_duration
                    dm_embed.add_field(name="Ende", value=discord.utils.format_dt(end_time, 'F'), inline=True)
                    dm_embed.set_footer(text="Bitte beachte die Serverregeln.")
                    
                    await member.send(embed=dm_embed)
                    notification_sent = True
                except discord.Forbidden:
                    pass  # DMs deaktiviert

            # Timeout durchführen
            timeout_reason = f"{reason} | Moderator: {ctx.author} ({ctx.author.id})"
            await member.timeout_for(parsed_duration, reason=timeout_reason)

            # Erfolgs-Embed
            additional_info = None
            if notification_sent:
                additional_info = "User per DM benachrichtigt"
            elif notify_user:
                additional_info = "DM-Benachrichtigung fehlgeschlagen"

            embed = self._create_moderation_embed(
                "Timeout", ctx.author, member, reason,
                duration=self._format_duration(parsed_duration),
                additional_info=additional_info
            )

            # Ende-Zeit hinzufügen
            end_time = datetime.now(timezone.utc) + parsed_duration
            embed.add_field(name="🕐 Ende", value=discord.utils.format_dt(end_time, 'F'), inline=False)

            await ctx.followup.send(embed=embed)
            self.logger.info(f"User {member} ({member.id}) timed out by {ctx.author} ({ctx.author.id}) for {duration}: {reason}")

        except discord.Forbidden:
            embed = self._create_error_embed(
                "Berechtigung verweigert",
                f"Mir fehlen die Berechtigungen, um {member.mention} zu timeouten.",
                "Stelle sicher, dass meine Rolle höher als die des Ziels ist."
            )
            await ctx.followup.send(embed=embed)
        except discord.HTTPException as e:
            embed = self._create_error_embed(
                "Discord-Fehler",
                f"Fehler beim Timeout: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
            self.logger.error(f"Unexpected error in timeout command: {e}", exc_info=True)

    # ✅ Verbesserter Untimeout Command
    @moderation.command(name="untimeout", description="Hebt einen Timeout auf")
    @option("member", discord.Member, description="Das Mitglied, dessen Timeout aufgehoben werden soll")
    @option("reason", str, description="Grund für die Aufhebung", max_length=500, required=False)
    @option("notify_user", bool, description="User per DM benachrichtigen?", required=False, default=True)
    async def untimeout(self, ctx: discord.ApplicationContext, member: discord.Member,
                        reason: str = "Kein Grund angegeben", notify_user: bool = True):

        await ctx.defer(ephemeral=True)

        try:
            # Berechtigung prüfen
            if not self._has_permission(ctx.author, MODERATE):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst die `Mitglieder moderieren` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Bot-Berechtigung prüfen
            if not self._has_permission(ctx.guild.me, MODERATE):
                embed = self._create_error_embed(
                    "Bot-Berechtigung fehlt",
                    "Mir fehlt die `Mitglieder moderieren` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Prüfen ob Mitglied überhaupt in Timeout ist
            if (member.communication_disabled_until is None or 
                member.communication_disabled_until <= datetime.now(timezone.utc)):
                embed = self._create_error_embed(
                    "Kein aktiver Timeout",
                    f"{member.mention} ist derzeit nicht in Timeout."
                )
                return await ctx.followup.send(embed=embed)

            # User benachrichtigen (vor der Aufhebung)
            notification_sent = False
            if notify_user:
                try:
                    dm_embed = discord.Embed(
                        title=f"{emoji_yes} Dein Timeout wurde aufgehoben",
                        color=SUCCESS_COLOR,
                        description=f"Dein Timeout auf **{ctx.guild.name}** wurde vorzeitig aufgehoben."
                    )
                    dm_embed.add_field(name="Grund", value=reason, inline=False)
                    dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=True)
                    dm_embed.set_footer(text="Bitte beachte weiterhin die Serverregeln.")
                    
                    await member.send(embed=dm_embed)
                    notification_sent = True
                except discord.Forbidden:
                    pass  # DMs deaktiviert

            # Timeout aufheben
            untimeout_reason = f"{reason} | Moderator: {ctx.author} ({ctx.author.id})"
            await member.remove_timeout(reason=untimeout_reason)

            # Erfolgs-Embed
            additional_info = None
            if notification_sent:
                additional_info = "User per DM benachrichtigt"
            elif notify_user:
                additional_info = "DM-Benachrichtigung fehlgeschlagen"

            embed = self._create_moderation_embed(
                "Timeout aufgehoben", ctx.author, member, reason,
                additional_info=additional_info
            )

            await ctx.followup.send(embed=embed)
            self.logger.info(f"Timeout removed from {member} ({member.id}) by {ctx.author} ({ctx.author.id}): {reason}")

        except discord.Forbidden:
            embed = self._create_error_embed(
                "Berechtigung verweigert",
                f"Mir fehlen die Berechtigungen, um den Timeout von {member.mention} aufzuheben."
            )
            await ctx.followup.send(embed=embed)
        except discord.HTTPException as e:
            embed = self._create_error_embed(
                "Discord-Fehler",
                f"Fehler beim Aufheben des Timeouts: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
            self.logger.error(f"Unexpected error in untimeout command: {e}", exc_info=True)

    # ✅ Verbesserter Slowmode Command
    @moderation.command(name="slowmode", description="Setzt den Slowmode für den aktuellen Channel")
    @option("duration", str, description="Dauer (z.B. 10s, 5m, 1h) oder '0' zum Deaktivieren", default="0")
    @option("reason", str, description="Grund für den Slowmode", max_length=500, required=False)
    async def slowmode(self, ctx: discord.ApplicationContext, duration: str = "0", 
                      reason: str = "Kein Grund angegeben"):

        await ctx.defer(ephemeral=True)

        try:
            # Berechtigung prüfen
            if not ctx.author.guild_permissions.manage_channels:
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst die `Kanäle verwalten` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Bot-Berechtigung prüfen
            if not ctx.guild.me.guild_permissions.manage_channels:
                embed = self._create_error_embed(
                    "Bot-Berechtigung fehlt",
                    "Mir fehlt die `Kanäle verwalten` Berechtigung."
                )
                return await ctx.followup.send(embed=embed)

            # Spezielle Behandlung für "0" (deaktivieren)
            if duration == "0":
                seconds = 0
            else:
                # Dauer parsen
                parsed_duration = self._parse_duration(duration)
                if parsed_duration is None:
                    embed = self._create_error_embed(
                        "Ungültige Dauer",
                        f"Konnte '{duration}' nicht als gültige Dauer erkennen.",
                        "Beispiele: `10s`, `5m`, `1h` oder `0` zum Deaktivieren"
                    )
                    return await ctx.followup.send(embed=embed)

                seconds = int(parsed_duration.total_seconds())

            # Discord Slowmode Limits: 0-21600 Sekunden (6 Stunden)
            if seconds < 0 or seconds > 21600:
                embed = self._create_error_embed(
                    "Ungültiger Zeitraum",
                    f"Slowmode muss zwischen 0 Sekunden und 6 Stunden liegen.",
                    f"Eingabe: {seconds} Sekunden"
                )
                return await ctx.followup.send(embed=embed)

            # Aktuellen Slowmode speichern für Vergleich
            old_slowmode = ctx.channel.slowmode_delay

            # Slowmode durchführen
            slowmode_reason = f"{reason} | Moderator: {ctx.author} ({ctx.author.id})"
            await ctx.channel.edit(slowmode_delay=seconds, reason=slowmode_reason)

            # Erfolgs-Embed
            if seconds == 0:
                action = "Slowmode deaktiviert"
                additional_info = f"Vorheriger Slowmode: {old_slowmode}s" if old_slowmode > 0 else None
            else:
                action = "Slowmode aktiviert"
                additional_info = f"Slowmode auf {seconds} Sekunden gesetzt"

            embed = self._create_moderation_embed(
                action, ctx.author, None, reason,
                duration=f"{seconds} Sekunden" if seconds > 0 else "Deaktiviert",
                additional_info=additional_info
            )
            embed.add_field(name="📢 Kanal", value=ctx.channel.mention, inline=True)

            await ctx.followup.send(embed=embed)
            self.logger.info(f"Slowmode set to {seconds}s in {ctx.channel} by {ctx.author} ({ctx.author.id}): {reason}")

        except discord.Forbidden:
            embed = self._create_error_embed(
                "Berechtigung verweigert",
                "Mir fehlen die Berechtigungen, um den Slowmode zu setzen."
            )
            await ctx.followup.send(embed=embed)
        except discord.HTTPException as e:
            embed = self._create_error_embed(
                "Discord-Fehler",
                f"Fehler beim Setzen des Slowmodes: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
            )
            await ctx.followup.send(embed=embed)
            self.logger.error(f"Unexpected error in slowmode command: {e}", exc_info=True)

    # ✅ Verbesserter Votekick Command
    @moderation.command(name="votekick", description="Startet eine Votekick-Abstimmung für ein Mitglied")
    @option("member", discord.Member, description="Das zu kickende Mitglied")
    @option("reason", str, description="Grund für den Kick", max_length=500, required=False)
    @option("duration", int, description="Abstimmungsdauer in Minuten (Standard: 5)", min_value=1, max_value=30, required=False)
    async def votekick(self, ctx: discord.ApplicationContext, member: discord.Member,
                       reason: str = "Kein Grund angegeben", duration: int = 5):

        await ctx.defer()

        try:
            # Berechtigung prüfen
            if not self._has_permission(ctx.author, KICK):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst die `Mitglieder kicken` Berechtigung."
                )
                return await ctx.followup.send(embed=embed, ephemeral=True)

            # Bot-Berechtigung prüfen
            if not self._has_permission(ctx.guild.me, KICK):
                embed = self._create_error_embed(
                    "Bot-Berechtigung fehlt",
                    "Mir fehlt die `Mitglieder kicken` Berechtigung."
                )
                return await ctx.followup.send(embed=embed, ephemeral=True)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = self._create_error_embed("Moderation nicht möglich", error_msg)
                return await ctx.followup.send(embed=embed, ephemeral=True)

            # Prüfen ob bereits eine Abstimmung für diesen User läuft
            if member.id in self._active_votes:
                embed = self._create_error_embed(
                    "Abstimmung bereits aktiv",
                    f"Es läuft bereits eine Abstimmung für {member.mention}."
                )
                return await ctx.followup.send(embed=embed, ephemeral=True)

            # Abstimmungs-Embed erstellen
            end_time = datetime.now(timezone.utc) + timedelta(minutes=duration)
            
            embed = discord.Embed(
                title=f"🗳️ Votekick für {member.display_name}",
                description=f"{ctx.author.mention} möchte {member.mention} kicken.\n\n"
                           f"**Grund:** {reason}\n\n"
                           f"Reagiere mit {emoji_yes} zum Kicken oder {emoji_no} zum Ablehnen.\n"
                           f"**Ende:** {discord.utils.format_dt(end_time, 'R')}",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_author(name=f"Gestartet von {ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.add_field(name="🎯 Ziel", value=f"{member.mention}", inline=True)
            embed.add_field(name="⏱️ Dauer", value=f"{duration} Minuten", inline=True)
            embed.set_footer(text=f"Votekick ID: {member.id}")

            # Nachricht senden und Reaktionen hinzufügen
            message = await ctx.followup.send(embed=embed)
            await message.add_reaction(emoji_yes)
            await message.add_reaction(emoji_no)

            # Abstimmung zu aktiven Votes hinzufügen
            self._active_votes[member.id] = {
                'message': message,
                'initiator': ctx.author,
                'target': member,
                'reason': reason,
                'end_time': end_time,
                'guild': ctx.guild
            }

            # Abstimmung in separater Task verwalten
            asyncio.create_task(self._handle_votekick(member.id, duration * 60))

        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Fehler bei der Votekick-Abstimmung: {str(e)}"
            )
            try:
                await ctx.followup.send(embed=embed, ephemeral=True)
            except:
                await ctx.respond(embed=embed, ephemeral=True)
            self.logger.error(f"Unexpected error in votekick command: {e}", exc_info=True)

    async def _handle_votekick(self, member_id: int, duration_seconds: int):
        """Verwaltet eine Votekick-Abstimmung"""
        await asyncio.sleep(duration_seconds)

        if member_id not in self._active_votes:
            return

        vote_data = self._active_votes[member_id]
        message = vote_data['message']
        target = vote_data['target']
        initiator = vote_data['initiator']
        reason = vote_data['reason']
        guild = vote_data['guild']

        try:
            # Nachricht neu laden um aktuelle Reaktionen zu bekommen
            message = await message.channel.fetch_message(message.id)

            yes_count = 0
            no_count = 0
            voters = set()

            for reaction in message.reactions:
                if str(reaction.emoji) == emoji_yes:
                    async for user in reaction.users():
                        if not user.bot and user.id not in voters:
                            yes_count += 1
                            voters.add(user.id)
                elif str(reaction.emoji) == emoji_no:
                    async for user in reaction.users():
                        if not user.bot and user.id not in voters:
                            no_count += 1
                            voters.add(user.id)

            # Benötigte Stimmen berechnen
            total_members = len([m for m in guild.members if not m.bot])
            required_votes = max(3, total_members // 4)  # Mindestens 3 oder 1/4 der Member

            # Ergebnis auswerten
            if yes_count >= required_votes and yes_count > no_count:
                # Votekick erfolgreich
                try:
                    kick_reason = f"Votekick | Grund: {reason} | Initiator: {initiator} | Ja: {yes_count}, Nein: {no_count}"
                    await target.kick(reason=kick_reason)

                    result_embed = discord.Embed(
                        title="✅ Votekick erfolgreich",
                        description=f"{target.mention} wurde gekickt.",
                        color=discord.Color.green(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    result_embed.add_field(name="📊 Ergebnis", 
                                         value=f"Ja: {yes_count} | Nein: {no_count}\nBenötigt: {required_votes}", 
                                         inline=False)

                    self.logger.info(f"Votekick successful: {target} ({target.id}) kicked with {yes_count} votes")

                except discord.Forbidden:
                    result_embed = discord.Embed(
                        title="❌ Votekick fehlgeschlagen",
                        description=f"Berechtigung fehlt, um {target.mention} zu kicken.",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
                except discord.HTTPException as e:
                    result_embed = discord.Embed(
                        title="❌ Votekick fehlgeschlagen",
                        description=f"Fehler beim Kicken: {str(e)}",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
            else:
                # Votekick abgelehnt
                result_embed = discord.Embed(
                    title="❌ Votekick abgelehnt",
                    description=f"{target.mention} wurde nicht gekickt.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                result_embed.add_field(name="📊 Ergebnis", 
                                     value=f"Ja: {yes_count} | Nein: {no_count}\nBenötigt: {required_votes}", 
                                     inline=False)

            await message.edit(embed=result_embed, view=None)

        except Exception as e:
            self.logger.error(f"Error handling votekick result: {e}", exc_info=True)
        finally:
            # Abstimmung aus aktiven Votes entfernen
            if member_id in self._active_votes:
                del self._active_votes[member_id]


def setup(bot):
    bot.add_cog(Moderation(bot))