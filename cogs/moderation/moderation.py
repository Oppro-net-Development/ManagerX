# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────

from FastCoding.backend import discord, ezcord, slash_command, option, timedelta, SlashCommandGroup
from FastCoding.backend import KICK, BAN, MODERATE
from FastCoding.ui import emoji_yes, emoji_no, emoji_user, ERROR_TITLE, ERROR_COLOR

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
            title=f"{emoji_yes} × {action} erfolgreich",
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
    @slash_command(name="ban", description="Bannt ein Mitglied vom Server")
    @option("member", discord.Member, description="Das zu bannende Mitglied")
    @option("reason", str, description="Grund für den Bann", required=False)
    @option("delete_messages", bool, description="Nachrichten der letzten 7 Tage löschen?", required=False,
            default=False)
    async def ban(self, ctx: discord.ApplicationContext, member: discord.Member,
                  reason: str = "Kein Grund angegeben", delete_messages: bool = False):

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

        try:
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

    # ✅ Kick Command
    @slash_command(name="kick", description="Kickt ein Mitglied vom Server")
    @option("member", discord.Member, description="Das zu kickende Mitglied")
    @option("reason", str, description="Grund für den Kick", required=False)
    async def kick(self, ctx: discord.ApplicationContext, member: discord.Member,
                   reason: str = "Kein Grund angegeben"):

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

        try:
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

    # ✅ Timeout Command
    @slash_command(name="timeout", description="Versetzt ein Mitglied in Timeout")
    @option("member", discord.Member, description="Das zu mutende Mitglied")
    @option("duration", str, description="Dauer (z.B. 10m, 1h30m, 2d)")
    @option("reason", str, description="Grund für den Timeout", required=False)
    async def timeout(self, ctx: discord.ApplicationContext, member: discord.Member,
                      duration: str, reason: str = "Kein Grund angegeben"):

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

        try:
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

    # ✅ Untimeout Command
    @slash_command(name="untimeout", description="Hebt einen Timeout auf")
    @option("member", discord.Member, description="Das Mitglied, dessen Timeout aufgehoben werden soll")
    @option("reason", str, description="Grund für die Aufhebung", required=False)
    async def untimeout(self, ctx: discord.ApplicationContext, member: discord.Member,
                        reason: str = "Kein Grund angegeben"):

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

        try:
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


def setup(bot):
    bot.add_cog(Moderation(bot))