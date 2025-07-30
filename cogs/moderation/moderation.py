# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────

from FastCoding.backend import discord, ezcord, slash_command, option, timedelta, SlashCommandGroup
from FastCoding.backend import KICK, BAN, MODERATE
from FastCoding.ui import emoji_yes, emoji_no, emoji_user, ERROR_TITLE, ERROR_COLOR

import asyncio
import re
from datetime import datetime
from typing import Optional


# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class Moderation(ezcord.Cog):
    """Erweiterte Moderations-Cog mit verbesserter Sicherheit und Fehlerbehandlung"""

    def __init__(self, bot):
        self.bot = bot
        # Maximale Timeout-Dauer (Discord Limit: 28 Tage)
        self.max_timeout_days = 28

    # SlashCommandGroup muss als Klassenattribut definiert werden
    moderation = SlashCommandGroup("moderation", "Moderationsbefehle")

    def _can_moderate_member(self, moderator: discord.Member, target: discord.Member) -> tuple[bool, str]:
        """Überprüft, ob ein Moderator ein Ziel-Mitglied moderieren kann"""

        # Bot-Owner kann nicht moderiert werden
        if target.id == target.guild.owner_id:
            return False, "Der Server-Owner kann nicht moderiert werden."

        # Selbst-Moderation verhindern
        if moderator.id == target.id:
            return False, "Du kannst dich nicht selbst moderieren."

        # Bot kann sich nicht selbst moderieren
        if target.id == self.bot.user.id:
            return False, "Ich kann mich nicht selbst moderieren."

        # Rollen-Hierarchie prüfen
        if moderator.top_role <= target.top_role and moderator.id != target.guild.owner_id:
            return False, "Du kannst keine Mitglieder mit gleicher oder höherer Rolle moderieren."

        # Bot-Berechtigung prüfen
        bot_member = target.guild.get_member(self.bot.user.id)
        if bot_member and bot_member.top_role <= target.top_role:
            return False, "Meine Rolle ist nicht hoch genug, um dieses Mitglied zu moderieren."

        return True, ""

    def _parse_duration(self, duration_str: str) -> Optional[timedelta]:
        """Erweiterte Dauer-Parsing mit mehr Formaten"""
        # Regex für verschiedene Formate: 1h30m, 2d, 45m, etc.
        pattern = r'(\d+)([smhd])'
        matches = re.findall(pattern, duration_str.lower())

        if not matches:
            return None

        total_seconds = 0

        for amount_str, unit in matches:
            try:
                amount = int(amount_str)
            except ValueError:
                return None

            if unit == 's':
                total_seconds += amount
            elif unit == 'm':
                total_seconds += amount * 60
            elif unit == 'h':
                total_seconds += amount * 3600
            elif unit == 'd':
                total_seconds += amount * 86400
            else:
                return None

        # Maximale Dauer prüfen
        max_seconds = self.max_timeout_days * 86400
        if total_seconds > max_seconds:
            return None

        return timedelta(seconds=total_seconds)

    def _create_log_embed(self, action: str, moderator: discord.Member, target: discord.Member,
                          reason: str, duration: str = None) -> discord.Embed:
        """Erstellt ein einheitliches Log-Embed"""
        embed = discord.Embed(
            title=f"{emoji_yes} {action} erfolgreich",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="Ziel", value=f"{emoji_user} {target.mention} ({target})", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)

        if duration:
            embed.add_field(name="Dauer", value=duration, inline=True)

        embed.add_field(name="Grund", value=reason, inline=False)
        embed.set_footer(text=f"User ID: {target.id}")

        return embed

    # ✅ Ban Command
    @moderation.command(name="ban", description="Bannt ein Mitglied vom Server")
    @option("member", discord.Member, description="Das zu bannende Mitglied")
    @option("reason", str, description="Grund für den Bann", required=False)
    @option("delete_messages", bool, description="Nachrichten der letzten 7 Tage löschen?", required=False,
            default=False)
    async def ban(self, ctx: discord.ApplicationContext, member: discord.Member,
                  reason: str = "Kein Grund angegeben", delete_messages: bool = False):

        try:
            # Berechtigung prüfen
            if not getattr(ctx.author.guild_permissions, BAN, False):
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Du benötigst die `Mitglieder bannen` Berechtigung.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} {error_msg}",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Bann durchführen
            delete_days = 7 if delete_messages else 0
            await member.ban(reason=f"{reason} | Moderator: {ctx.author}", delete_message_days=delete_days)

            # Erfolgs-Embed
            embed = self._create_log_embed("Bann", ctx.author, member, reason)
            if delete_messages:
                embed.add_field(name="Nachrichten", value="Nachrichten der letzten 7 Tage gelöscht", inline=False)

            await ctx.respond(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Mir fehlen die Berechtigungen, um {member.mention} zu bannen.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Fehler beim Bannen: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Unerwarteter Fehler: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)

    # ✅ Kick Command
    @moderation.command(name="kick", description="Kickt ein Mitglied vom Server")
    @option("member", discord.Member, description="Das zu kickende Mitglied")
    @option("reason", str, description="Grund für den Kick", required=False)
    async def kick(self, ctx: discord.ApplicationContext, member: discord.Member,
                   reason: str = "Kein Grund angegeben"):
        try:
            # Berechtigung prüfen
            if not getattr(ctx.author.guild_permissions, KICK, False):
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Du benötigst die `Mitglieder kicken` Berechtigung.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} {error_msg}",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Kick durchführen
            await member.kick(reason=f"{reason} | Moderator: {ctx.author}")

            # Erfolgs-Embed
            embed = self._create_log_embed("Kick", ctx.author, member, reason)
            await ctx.respond(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Mir fehlen die Berechtigungen, um {member.mention} zu kicken.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Fehler beim Kicken: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Unerwarteter Fehler: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)

    # ✅ Timeout Command
    @moderation.command(name="timeout", description="Versetzt ein Mitglied in Timeout")
    @option("member", discord.Member, description="Das zu mutende Mitglied")
    @option("duration", str, description="Dauer (z.B. 10m, 1h30m, 2d)")
    @option("reason", str, description="Grund für den Timeout", required=False)
    async def timeout(self, ctx: discord.ApplicationContext, member: discord.Member,
                      duration: str, reason: str = "Kein Grund angegeben"):

        try:
            # Berechtigung prüfen
            if not getattr(ctx.author.guild_permissions, MODERATE, False):
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Du benötigst die `Mitglieder moderieren` Berechtigung.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} {error_msg}",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Dauer parsen
            parsed_duration = self._parse_duration(duration)
            if parsed_duration is None:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Ungültige Dauer! Beispiele: `10m`, `1h30m`, `2d`\nMaximum: {self.max_timeout_days} Tage",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Minimale Dauer prüfen (1 Sekunde)
            if parsed_duration.total_seconds() < 1:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Die Timeout-Dauer muss mindestens 1 Sekunde betragen.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Timeout durchführen
            await member.timeout_for(parsed_duration, reason=f"{reason} | Moderator: {ctx.author}")

            # Erfolgs-Embed
            embed = self._create_log_embed("Timeout", ctx.author, member, reason, duration)
            await ctx.respond(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Mir fehlen die Berechtigungen, um {member.mention} zu timeouten.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Fehler beim Timeout: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Unerwarteter Fehler: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)

    # ✅ Untimeout Command
    @moderation.command(name="untimeout", description="Hebt einen Timeout auf")
    @option("member", discord.Member, description="Das Mitglied, dessen Timeout aufgehoben werden soll")
    @option("reason", str, description="Grund für die Aufhebung", required=False)
    async def untimeout(self, ctx: discord.ApplicationContext, member: discord.Member,
                        reason: str = "Kein Grund angegeben"):

        try:
            # Berechtigung prüfen
            if not getattr(ctx.author.guild_permissions, MODERATE, False):
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Du benötigst die `Mitglieder moderieren` Berechtigung.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Prüfen ob Mitglied überhaupt in Timeout ist
            if member.communication_disabled_until is None:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} {member.mention} ist nicht in Timeout.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Timeout aufheben
            await member.remove_timeout(reason=f"{reason} | Moderator: {ctx.author}")

            # Erfolgs-Embed
            embed = self._create_log_embed("Timeout aufgehoben", ctx.author, member, reason)
            await ctx.respond(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Mir fehlen die Berechtigungen, um den Timeout von {member.mention} aufzuheben.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Fehler beim Aufheben des Timeouts: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Unerwarteter Fehler: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @moderation.command(name="votekick", description="Startet eine Votekick-Abstimmung für ein Mitglied")
    @option("member", discord.Member, description="Das zu kickende Mitglied")
    @option("reason", str, description="Grund für den Kick", required=False)
    async def votekick(self, ctx: discord.ApplicationContext, member: discord.Member,
                       reason: str = "Kein Grund angegeben"):
        """Startet eine Votekick-Abstimmung für ein Mitglied"""
        try:
            # Berechtigung prüfen
            if not getattr(ctx.author.guild_permissions, KICK, False):
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Du benötigst die `Mitglieder kicken` Berechtigung.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Moderation möglich?
            can_moderate, error_msg = self._can_moderate_member(ctx.author, member)
            if not can_moderate:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} {error_msg}",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Votekick-Embed erstellen
            embed = discord.Embed(
                title=f"Votekick für {member.name}",
                description=f"{ctx.author.mention} möchte {member.mention} kicken.\n\n"
                            f"Grund: {reason}\n\nReagiere mit ✅ zum Kicken oder ❌ zum Ablehnen.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"User ID: {member.id}")

            # Respond first, then get the message
            await ctx.respond(embed=embed)
            message = await ctx.original_response()

            # Reaktionen hinzufügen
            await message.add_reaction(emoji_yes)
            await message.add_reaction(emoji_no)

            # Warten auf Reaktionen (5 Minuten)
            def check(reaction, user):
                return (user != self.bot.user and
                        str(reaction.emoji) in [emoji_yes, emoji_no] and
                        reaction.message.id == message.id)

            # Warte auf mehrere Reaktionen über die gesamte Zeit
            end_time = asyncio.get_event_loop().time() + 300.0  # 5 Minuten

            while asyncio.get_event_loop().time() < end_time:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add',
                                                             timeout=end_time - asyncio.get_event_loop().time(),
                                                             check=check)
                except asyncio.TimeoutError:
                    break

            # Nach 5 Minuten: Reaktionen zählen
            # Message neu laden um aktuelle Reaktionen zu bekommen
            message = await ctx.channel.fetch_message(message.id)

            yes_count = 0
            no_count = 0

            for reaction in message.reactions:
                if str(reaction.emoji) == emoji_yes:
                    # Zähle nur echte User (nicht den Bot)
                    users = [user async for user in reaction.users() if user != self.bot.user]
                    yes_count = len(users)
                elif str(reaction.emoji) == emoji_no:
                    users = [user async for user in reaction.users() if user != self.bot.user]
                    no_count = len(users)

            # Prüfen ob genug Ja-Stimmen
            total_members = len([m for m in ctx.guild.members if not m.bot])  # Nur echte User zählen
            required_votes = max(3, total_members // 3)  # Mindestens 3 Stimmen oder 1/3 der Member

            if yes_count >= required_votes and yes_count > no_count:
                try:
                    # Kick durchführen
                    await member.kick(reason=f"Votekick | Grund: {reason} | Moderator: {ctx.author}")

                    embed = discord.Embed(
                        title="✅ Votekick erfolgreich",
                        description=f"{member.mention} wurde gekickt.\n\n"
                                    f"Ja-Stimmen: {yes_count}, Nein-Stimmen: {no_count}\n"
                                    f"Benötigt: {required_votes}",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    await ctx.followup.send(embed=embed)

                except discord.Forbidden:
                    embed = discord.Embed(
                        title=ERROR_TITLE,
                        description=f"{emoji_no} Mir fehlen die Berechtigungen, um {member.mention} zu kicken.",
                        color=ERROR_COLOR
                    )
                    await ctx.followup.send(embed=embed)
                except discord.HTTPException as e:
                    embed = discord.Embed(
                        title=ERROR_TITLE,
                        description=f"{emoji_no} Fehler beim Kicken: {str(e)}",
                        color=ERROR_COLOR
                    )
                    await ctx.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Votekick abgelehnt",
                    description=f"{member.mention} wurde nicht gekickt.\n\n"
                                f"Ja-Stimmen: {yes_count}, Nein-Stimmen: {no_count}\n"
                                f"Benötigt: {required_votes}",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                await ctx.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Fehler bei der Votekick-Abstimmung: {str(e)}",
                color=ERROR_COLOR
            )
            try:
                await ctx.followup.send(embed=embed)
            except:
                await ctx.respond(embed=embed, ephemeral=True)

    @moderation.command(name="slowmode", description="Setzt den Slowmode für den aktuellen Channel")
    @option("time", str, description="Dauer (z.B. 10s, 5m, 1h)", default="1h")
    @option("reason", str, description="Grund für den Slowmode", required=False)
    async def slowmode(self, ctx: discord.ApplicationContext, time: str = "1h", reason: str = "Kein Grund angegeben"):
        """Setzt den Slowmode für den aktuellen Channel"""
        try:
            # Berechtigung prüfen - für Slowmode benötigt man "Manage Channels"
            if not ctx.author.guild_permissions.manage_channels:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Du benötigst die `Kanäle verwalten` Berechtigung.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Dauer parsen
            parsed_duration = self._parse_duration(time)
            if parsed_duration is None:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Ungültige Dauer! Beispiele: `10s`, `5m`, `1h`",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Discord Slowmode Limits: 0-21600 Sekunden (6 Stunden)
            seconds = int(parsed_duration.total_seconds())
            if seconds < 0 or seconds > 21600:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=f"{emoji_no} Slowmode muss zwischen 0 Sekunden und 6 Stunden liegen.",
                    color=ERROR_COLOR
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Slowmode durchführen
            await ctx.channel.edit(slowmode_delay=seconds, reason=f"{reason} | Moderator: {ctx.author}")

            # Erfolgs-Embed
            if seconds == 0:
                embed = discord.Embed(
                    title="✅ Slowmode deaktiviert",
                    description=f"Slowmode für {ctx.channel.mention} wurde deaktiviert.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
            else:
                embed = discord.Embed(
                    title="✅ Slowmode erfolgreich",
                    description=f"Slowmode für {ctx.channel.mention} auf {time} gesetzt.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Dauer", value=f"{seconds} Sekunden", inline=True)
                embed.add_field(name="Grund", value=reason, inline=True)

            await ctx.respond(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Mir fehlen die Berechtigungen, um den Slowmode zu setzen.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Fehler beim Setzen des Slowmodes: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Unerwarteter Fehler: {str(e)}",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)


# ───────────────────────────────────────────────

def setup(bot):
    bot.add_cog(Moderation(bot))