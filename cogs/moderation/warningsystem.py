# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
from DevTools.ui import (
    emoji_no, emoji_yes, emoji_warn, emoji_member, emoji_staff, emoji_slowmode, emoji_summary, ERROR_TITLE, 
    ERROR_COLOR, SUCCESS_COLOR, AUTHOR, FLOOTER
)
from DevTools.backend import WarnDatabase
from DevTools.backend import discord, slash_command, Option, datetime, os, ezcord
import asyncio
from typing import Optional

# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class WarnSystem(ezcord.Cog, group="moderation"):
    """Erweiterte Warn-System Cog mit verbesserter Funktionalität"""
    
    def __init__(self, bot):
        self.bot = bot
        base_path = os.path.dirname(__file__)
        self.db = WarnDatabase(base_path)
        # Cache für bessere Performance
        self._warn_cache = {}

    def _has_moderate_permissions(self, member: discord.Member) -> bool:
        """Überprüft ob ein Member Moderationsrechte hat"""
        return (
            member.guild_permissions.kick_members or
            member.guild_permissions.ban_members or
            member.guild_permissions.manage_messages or
            member.guild_permissions.moderate_members
        )

    def _can_warn_member(self, moderator: discord.Member, target: discord.Member) -> tuple[bool, str]:
        """Überprüft ob ein Moderator ein Ziel-Mitglied verwarnen kann"""
        
        # Server-Owner kann nicht verwarnt werden
        if target.id == target.guild.owner_id:
            return False, "Der Server-Owner kann nicht verwarnt werden."
        
        # Selbst-Verwarnung verhindern
        if moderator.id == target.id:
            return False, "Du kannst dich nicht selbst verwarnen."
        
        # Bot kann nicht verwarnt werden
        if target.bot:
            return False, "Bots können nicht verwarnt werden."
        
        # Rollen-Hierarchie prüfen (außer bei Owner)
        if (moderator.top_role <= target.top_role and 
            moderator.id != target.guild.owner_id):
            return False, "Du kannst keine Mitglieder mit gleicher oder höherer Rolle verwarnen."
        
        return True, ""

    def _create_warn_embed(self, action: str, moderator: discord.Member, 
                          target: discord.Member, reason: str, 
                          timestamp: str, warn_id: int = None) -> discord.Embed:
        """Erstellt ein einheitliches Warn-Embed"""
        
        if action == "warn":
            embed = discord.Embed(
                title=f"{emoji_warn} Warnung erteilt",
                color=SUCCESS_COLOR,
                description=f"{target.mention} wurde erfolgreich verwarnt."
            )
        elif action == "unwarn":
            embed = discord.Embed(
                title=f"{emoji_yes} Warnung entfernt",
                color=SUCCESS_COLOR,
                description=f"Warnung wurde erfolgreich entfernt."
            )
        else:
            embed = discord.Embed(
                title=f" {action}",
                color=SUCCESS_COLOR
            )
        
        embed.set_author(name=AUTHOR)
        
        if action == "warn":
            embed.add_field(name=f"{emoji_member} × Verwarnter User", value=target.mention, inline=True)
            embed.add_field(name=f"{emoji_staff} × Verwarnt von", value=moderator.mention, inline=True)
            embed.add_field(name=f"{emoji_summary} × Grund", value=reason, inline=False)
            embed.add_field(name=f"{emoji_slowmode} × Zeitstempel", value=timestamp, inline=False)
            embed.set_footer(text="Powered by ManagerX")
        
        elif action == "unwarn":
            embed.add_field(name=f" Entfernt von", value=moderator.mention, inline=True)
            if warn_id:
                embed.add_field(name=f" Warnung ID", value=f"`{warn_id}`", inline=True)
            embed.set_footer(text=FLOOTER)
        
        return embed

    def _create_error_embed(self, title: str, message: str) -> discord.Embed:
        """Erstellt ein einheitliches Error-Embed"""
        embed = discord.Embed(title=title, color=ERROR_COLOR)
        embed.set_author(name=AUTHOR)
        embed.add_field(name=f"{emoji_no} {title}", value=message, inline=False)
        embed.set_footer(text=FLOOTER)
        return embed

    @slash_command(name="warn", description="Warnen Sie einen Benutzer")
    async def warn(
        self,
        ctx,
        user: Option(discord.Member, "User to warn"),
        reason: Option(str, "Reason for the warning", max_length=500)
    ):
        try:
            # Berechtigung prüfen
            if not self._has_moderate_permissions(ctx.author):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst Moderationsrechte, um Mitglieder zu verwarnen."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Kann Mitglied verwarnt werden?
            can_warn, error_msg = self._can_warn_member(ctx.author, user)
            if not can_warn:
                embed = self._create_error_embed("Verwarnung nicht möglich", error_msg)
                return await ctx.respond(embed=embed, ephemeral=True)

            # Warn-Daten erstellen
            timestamp = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M")
            
            # In Datenbank speichern
            try:
                self.db.add_warning(ctx.guild.id, user.id, ctx.author.id, reason, timestamp)
                
                # Cache invalidieren
                cache_key = f"{ctx.guild.id}_{user.id}"
                if cache_key in self._warn_cache:
                    del self._warn_cache[cache_key]
                
            except Exception as e:
                embed = self._create_error_embed(
                    "Datenbankfehler",
                    f"Fehler beim Speichern der Warnung: {str(e)}"
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Erfolgs-Embed
            success_embed = self._create_warn_embed("warn", ctx.author, user, reason, timestamp)
            await ctx.respond(embed=success_embed, ephemeral=True)

            # Optional: DM an verwarnten User senden
            try:
                dm_embed = discord.Embed(
                    title=f"{emoji_warn} Du wurdest verwarnt",
                    color=ERROR_COLOR,
                    description=f"Du wurdest auf **{ctx.guild.name}** verwarnt."
                )
                dm_embed.add_field(name=f"{emoji_summary} × Grund", value=reason, inline=False)
                dm_embed.add_field(name=f"{emoji_staff} × Moderator", value=str(ctx.author), inline=True)
                dm_embed.add_field(name=f"{emoji_slowmode} × Zeitpunkt", value=timestamp, inline=True)
                dm_embed.set_footer(text="Powered by ManagerX")
                
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                # User hat DMs deaktiviert - ignorieren
                pass

        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="warnings", description="Zeigt die Verwarnungen eines Users an")
    async def warnings(
        self,
        ctx,
        user: Option(discord.Member, "User whose warnings to show", required=False)
    ):
        try:
            # Wenn kein User angegeben, eigene Warnungen zeigen
            target_user = user if user else ctx.author
            
            # Cache prüfen
            cache_key = f"{ctx.guild.id}_{target_user.id}"
            
            if cache_key in self._warn_cache:
                results = self._warn_cache[cache_key]
            else:
                # Warnungen aus Datenbank laden
                results = self.db.get_warnings(ctx.guild.id, target_user.id)
                self._warn_cache[cache_key] = results

            # Überprüfung ob User Warnungen einsehen darf
            if target_user != ctx.author and not self._has_moderate_permissions(ctx.author):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du kannst nur deine eigenen Warnungen einsehen."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            if not results:
                # Keine Warnungen vorhanden
                no_warnings_embed = discord.Embed(
                    title=f"{emoji_circleinfo} Keine Verwarnungen",
                    color=SUCCESS_COLOR,
                    description=f"{target_user.mention} hat keine Verwarnungen."
                )
                no_warnings_embed.set_author(name=AUTHOR)
                no_warnings_embed.set_footer(text=FLOOTER)
                return await ctx.respond(embed=no_warnings_embed, ephemeral=True)

            # Warnungen-Liste aufteilen falls zu viele (max 10 pro Seite)
            warnings_per_page = 10
            total_warnings = len(results)
            total_pages = (total_warnings + warnings_per_page - 1) // warnings_per_page

            if total_pages == 1:
                # Alle Warnungen auf einer Seite
                warn_list = "\n".join([
                    f"**ID `{warn_id}`** | {timestamp}\n└ **Grund:** {reason[:100]}{'...' if len(reason) > 100 else ''}"
                    for warn_id, reason, timestamp in results[:warnings_per_page]
                ])

                warnings_embed = discord.Embed(
                    title=f"{emoji_warn} Verwarnungen für {target_user.display_name}",
                    color=ERROR_COLOR,
                    description=warn_list
                )
                warnings_embed.set_author(name=AUTHOR)
                warnings_embed.add_field(name=f"{emoji_member} User", value=target_user.mention, inline=True)
                warnings_embed.add_field(name=f"{emoji_summary} Anzahl Verwarnungen", value=str(total_warnings), inline=True)
                warnings_embed.set_footer(text=FLOOTER)

                await ctx.respond(embed=warnings_embed, ephemeral=True)
            else:
                # Mehrere Seiten - ersten 10 zeigen mit Navigation
                await self._send_paginated_warnings(ctx, target_user, results, 0)

        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Fehler beim Laden der Warnungen: {str(e)}"
            )
            await ctx.respond(embed=embed, ephemeral=True)

    async def _send_paginated_warnings(self, ctx, target_user: discord.Member, 
                                     warnings: list, page: int = 0):
        """Sendet paginierte Warnungen mit Navigation"""
        warnings_per_page = 10
        total_pages = (len(warnings) + warnings_per_page - 1) // warnings_per_page
        
        start_idx = page * warnings_per_page
        end_idx = min(start_idx + warnings_per_page, len(warnings))
        page_warnings = warnings[start_idx:end_idx]
        
        warn_list = "\n".join([
            f"**ID `{warn_id}`** | {timestamp}\n└ **Grund:** {reason[:100]}{'...' if len(reason) > 100 else ''}"
            for warn_id, reason, timestamp in page_warnings
        ])

        embed = discord.Embed(
            title=f"{emoji_warn} Verwarnungen für {target_user.display_name}",
            color=ERROR_COLOR,
            description=warn_list
        )
        embed.set_author(name=AUTHOR)
        embed.add_field(name=f"{emoji_member} User", value=target_user.mention, inline=True)
        embed.add_field(name=f"{emoji_summary} Anzahl Verwarnungen", value=str(len(warnings)), inline=True)
        embed.set_footer(text=f"Seite {page + 1}/{total_pages} • {FLOOTER}")

        # View für Navigation erstellen
        view = WarningsView(self, target_user, warnings, page, total_pages)
        
        if ctx.response.is_done():
            await ctx.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.respond(embed=embed, view=view, ephemeral=True)

    @slash_command(name="unwarn", description="Löscht eine Verwarnung mit ID")
    async def unwarn(
        self,
        ctx,
        warn_id: Option(int, "Die ID der Verwarnung", min_value=1)
    ):
        try:
            # Berechtigung prüfen
            if not self._has_moderate_permissions(ctx.author):
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst Moderationsrechte, um Verwarnungen zu löschen."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Warnung suchen
            result = self.db.get_warning_by_id(warn_id)
            if not result:
                embed = self._create_error_embed(
                    "Verwarnung nicht gefunden",
                    f"Keine Verwarnung mit der ID `{warn_id}` gefunden."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Überprüfen ob Warnung zu diesem Server gehört
            warn_guild_id = result[1]  # guild_id ist der zweite Wert
            if warn_guild_id != ctx.guild.id:
                embed = self._create_error_embed(
                    "Verwarnung nicht gefunden",
                    f"Keine Verwarnung mit der ID `{warn_id}` in diesem Server gefunden."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Warnung löschen
            success = self.db.delete_warning(warn_id)
            if not success:
                embed = self._create_error_embed(
                    "Löschfehler",
                    f"Fehler beim Löschen der Verwarnung `{warn_id}`."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Cache invalidieren
            user_id = result[2]  # user_id ist der dritte Wert
            cache_key = f"{ctx.guild.id}_{user_id}"
            if cache_key in self._warn_cache:
                del self._warn_cache[cache_key]

            # Erfolgs-Embed
            removal_embed = self._create_warn_embed("unwarn", ctx.author, None, None, None, warn_id)
            await ctx.respond(embed=removal_embed, ephemeral=True)

        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Fehler beim Löschen der Verwarnung: {str(e)}"
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="clearwarns", description="Löscht alle Verwarnungen eines Users")
    async def clearwarns(
        self,
        ctx,
        user: Option(discord.Member, "User dessen Warnungen gelöscht werden sollen"),
        reason: Option(str, "Grund für das Löschen", required=False, default="Kein Grund angegeben")
    ):
        try:
            # Nur Administratoren können alle Warnungen löschen
            if not ctx.author.guild_permissions.administrator:
                embed = self._create_error_embed(
                    "Keine Berechtigung",
                    "Du benötigst Administrator-Rechte, um alle Warnungen zu löschen."
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            # Aktuelle Warnungen zählen
            warn_count = self.db.get_warning_count(ctx.guild.id, user.id)
            
            if warn_count == 0:
                embed = discord.Embed(
                    title=f"{emoji_summary} Keine Verwarnungen",
                    color=SUCCESS_COLOR,
                    description=f"{user.mention} hat keine Verwarnungen zum Löschen."
                )
                embed.set_author(name=AUTHOR)
                return await ctx.respond(embed=embed, ephemeral=True)

            # Bestätigung anfordern
            confirm_embed = discord.Embed(
                title=f"{emoji_warn} Bestätigung erforderlich",
                color=ERROR_COLOR,
                description=f"Möchtest du wirklich **{warn_count}** Warnungen von {user.mention} löschen?\n\n**Grund:** {reason}"
            )
            confirm_embed.set_footer(text="Diese Aktion kann nicht rückgängig gemacht werden! × Powered by ManagerX")

            view = ClearWarningsConfirmView(self, user, ctx.author, reason, warn_count)
            await ctx.respond(embed=confirm_embed, view=view, ephemeral=True)

        except Exception as e:
            embed = self._create_error_embed(
                "Unerwarteter Fehler",
                f"Fehler beim Vorbereiten der Löschung: {str(e)}"
            )
            await ctx.respond(embed=embed, ephemeral=True)

    async def clear_all_user_warnings(self, guild_id: int, user_id: int) -> int:
        """Löscht alle Warnungen eines Users und gibt die Anzahl zurück"""
        try:
            # Alle Warn-IDs für den User holen
            warnings = self.db.get_warnings(guild_id, user_id)
            deleted_count = 0
            
            for warn_id, _, _ in warnings:
                if self.db.delete_warning(warn_id):
                    deleted_count += 1
            
            # Cache invalidieren
            cache_key = f"{guild_id}_{user_id}"
            if cache_key in self._warn_cache:
                del self._warn_cache[cache_key]
            
            return deleted_count
            
        except Exception as e:
            print(f"Fehler beim Löschen aller Warnungen: {e}")
            return 0


class WarningsView(discord.ui.View):
    """View für die Navigation durch paginierte Warnungen"""
    
    def __init__(self, cog, target_user: discord.Member, warnings: list, current_page: int, total_pages: int):
        super().__init__(timeout=300)  # 5 Minuten Timeout
        self.cog = cog
        self.target_user = target_user
        self.warnings = warnings
        self.current_page = current_page
        self.total_pages = total_pages
        
        # Buttons aktivieren/deaktivieren
        self.previous_button.disabled = current_page == 0
        self.next_button.disabled = current_page >= total_pages - 1

    @discord.ui.button(label="◀ Vorherige", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self._update_page(interaction)

    @discord.ui.button(label="Nächste ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self._update_page(interaction)

    async def _update_page(self, interaction: discord.Interaction):
        """Aktualisiert die angezeigte Seite"""
        warnings_per_page = 10
        start_idx = self.current_page * warnings_per_page
        end_idx = min(start_idx + warnings_per_page, len(self.warnings))
        page_warnings = self.warnings[start_idx:end_idx]
        
        warn_list = "\n".join([
            f"**ID `{warn_id}`** | {timestamp}\n└ **Grund:** {reason[:100]}{'...' if len(reason) > 100 else ''}"
            for warn_id, reason, timestamp in page_warnings
        ])

        embed = discord.Embed(
            title=f"{emoji_warn} Verwarnungen für {self.target_user.display_name}",
            color=ERROR_COLOR,
            description=warn_list
        )
        embed.set_author(name=AUTHOR)
        embed.add_field(name=f"{emoji_member} User", value=self.target_user.mention, inline=True)
        embed.add_field(name=f"{emoji_summary} Anzahl Verwarnungen", value=str(len(self.warnings)), inline=True)
        embed.set_footer(text=f"Seite {self.current_page + 1}/{self.total_pages} • {FLOOTER}")

        # Buttons aktualisieren
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        """Deaktiviert alle Buttons nach Timeout"""
        for item in self.children:
            item.disabled = True


class ClearWarningsConfirmView(discord.ui.View):
    """View für die Bestätigung beim Löschen aller Warnungen"""
    
    def __init__(self, cog, target_user: discord.Member, moderator: discord.Member, reason: str, warn_count: int):
        super().__init__(timeout=60)  # 1 Minute Timeout
        self.cog = cog
        self.target_user = target_user
        self.moderator = moderator
        self.reason = reason
        self.warn_count = warn_count

    @discord.ui.button(label="✅ Bestätigen", style=discord.ButtonStyle.danger)
    async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Überprüfen ob der richtige User geantwortet hat
        if interaction.user.id != self.moderator.id:
            await interaction.response.send_message(
                "❌ Nur der ursprüngliche Moderator kann diese Aktion bestätigen.",
                ephemeral=True
            )
            return

        try:
            # Alle Warnungen löschen
            deleted_count = await self.cog.clear_all_user_warnings(
                interaction.guild.id, self.target_user.id
            )

            if deleted_count > 0:
                success_embed = discord.Embed(
                    title=f"{emoji_yes} Warnungen gelöscht",
                    color=SUCCESS_COLOR,
                    description=f"**{deleted_count}** Warnungen von {self.target_user.mention} wurden gelöscht."
                )
                success_embed.add_field(name="Grund", value=self.reason, inline=False)
                success_embed.add_field(name="Moderator", value=self.moderator.mention, inline=True)
                success_embed.set_footer(text=FLOOTER)
            else:
                success_embed = discord.Embed(
                    title=f"{emoji_no} Keine Warnungen gelöscht",
                    color=ERROR_COLOR,
                    description="Es konnten keine Warnungen gelöscht werden."
                )

            # View deaktivieren
            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(embed=success_embed, view=self)

        except Exception as e:
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR,
                description=f"Fehler beim Löschen: {str(e)}"
            )
            await interaction.response.edit_message(embed=error_embed, view=None)

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Überprüfen ob der richtige User geantwortet hat
        if interaction.user.id != self.moderator.id:
            await interaction.response.send_message(
                "❌ Nur der ursprüngliche Moderator kann diese Aktion abbrechen.",
                ephemeral=True
            )
            return

        cancel_embed = discord.Embed(
            title=f"{emoji_yes} Abgebrochen",
            color=SUCCESS_COLOR,
            description="Das Löschen der Warnungen wurde abgebrochen."
        )

        # View deaktivieren
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=cancel_embed, view=self)

    async def on_timeout(self):
        """Deaktiviert alle Buttons nach Timeout"""
        for item in self.children:
            item.disabled = True


def setup(bot):
    bot.add_cog(WarnSystem(bot))