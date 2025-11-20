# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord import SlashCommandGroup, Option
from discord.ext import commands, tasks
import time
import random
from DevTools import LevelDatabase
import asyncio
import io
import csv
from typing import Optional
from discord.ui import Container


class PrestigeConfirmView(discord.ui.View):
    def __init__(self, db, user, guild):
        super().__init__(timeout=300)
        self.db = db
        self.user = user
        self.guild = guild

    @discord.ui.button(label="Bestätigen", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm_prestige(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("Nur der User kann sein eigenes Prestige bestätigen!", ephemeral=True)
            return

        success = self.db.prestige_user(self.user.id, self.guild.id)
        if success:
            embed = discord.Embed(
                title="✨ Prestige erfolgreich!",
                description=f"{self.user.mention} hat ein Prestige durchgeführt!\nDu startest wieder bei Level 0, aber behältst deinen Prestige-Rang!",
                color=0xff69b4
            )
            embed.set_footer(text="Gratulation zu deinem Prestige!")
        else:
            embed = discord.Embed(
                title="❌ Prestige fehlgeschlagen",
                description="Prestige konnte nicht durchgeführt werden. Möglicherweise erfüllst du nicht die Anforderungen.",
                color=0xff0000
            )

        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel_prestige(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("Nur der User kann seine eigene Aktion abbrechen!", ephemeral=True)
            return

        embed = discord.Embed(
            title="❌ Prestige abgebrochen",
            description="Das Prestige wurde abgebrochen.",
            color=0x999999
        )
        await interaction.response.edit_message(embed=embed, view=None)


class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = LevelDatabase()
        self.xp_cooldowns = {}  # User-ID -> Timestamp
        
        # Starte Background Tasks
        self.cleanup_expired_boosts.start()
        self.cleanup_temporary_roles.start()

    def cog_unload(self):
        """Cleanup beim Entladen der Cog"""
        self.cleanup_expired_boosts.cancel()
        self.cleanup_temporary_roles.cancel()

    levelsystem = SlashCommandGroup("levelsystem", "Verwalte das Levelsystem")
    levelrole = SlashCommandGroup("levelrole", "Verwalte Level-Rollen")
    xpboost = SlashCommandGroup("xpboost", "Verwalte XP-Boosts")
    levelconfig = SlashCommandGroup("levelconfig", "Konfiguriere das Levelsystem")

    @tasks.loop(hours=1)
    async def cleanup_expired_boosts(self):
        """Entfernt abgelaufene XP-Boosts"""
        # Hier würde die DB-Cleanup Logik implementiert werden
        pass

    @tasks.loop(hours=1)
    async def cleanup_temporary_roles(self):
        """Entfernt abgelaufene temporäre Rollen"""
        # Hier würde die temporäre Rollen Cleanup Logik implementiert werden
        pass

    def create_level_up_embed(self, user: discord.Member, level: int, is_role_reward: bool = False, role: Optional[discord.Role] = None):
        """Erstellt ein verbessertes Level-Up Embed"""
        embed = discord.Embed(color=0x00ff00)
        embed.set_author(name="🎉 Level Up!", icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.description = f"**{user.mention}** erreichte **Level {level}**!"
        
        if is_role_reward and role:
            embed.add_field(name="🏆 Neue Rolle erhalten", value=f"**{role.name}**", inline=False)
            embed.color = 0xffff00
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        return embed

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignoriere Bot-Nachrichten
        if message.author.bot:
            return

        # Nur in Servern, nicht in DMs
        if message.guild is None:
            return

        # Prüfe ob Levelsystem aktiviert ist
        if not self.db.is_levelsystem_enabled(message.guild.id):
            return

        # Prüfe ob Kanal auf Blacklist steht
        if self.db.is_channel_blacklisted(message.guild.id, message.channel.id):
            return

        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()

        # Guild-Konfiguration holen
        config = self.db.get_guild_config(guild_id)
        cooldown = config.get('cooldown', 30)

        # XP-Cooldown prüfen
        if user_id in self.xp_cooldowns:
            if current_time - self.xp_cooldowns[user_id] < cooldown:
                return

        # Kanal-spezifischen Multiplikator anwenden
        channel_multiplier = self.db.get_channel_multiplier(guild_id, message.channel.id)
        
        # XP berechnen
        min_xp = config.get('min_xp', 10)
        max_xp = config.get('max_xp', 20)
        base_xp = random.randint(min_xp, max_xp)
        final_xp = int(base_xp * channel_multiplier)

        # XP hinzufügen mit Anti-Spam Protection
        level_up, new_level = self.db.add_xp(user_id, guild_id, final_xp, message.content)

        if not level_up and new_level == 0:
            return  # Anti-Spam blockierte die XP

        # Cooldown setzen
        self.xp_cooldowns[user_id] = current_time

        # Level Up Behandlung
        if level_up:
            # Bestimme Zielkanal für Level-Up Nachrichten
            target_channel = message.channel
            level_up_channel_id = config.get('level_up_channel')
            
            if level_up_channel_id:
                level_up_channel = message.guild.get_channel(level_up_channel_id)
                if level_up_channel:
                    target_channel = level_up_channel

            embed = self.create_level_up_embed(message.author, new_level)
            await target_channel.send(embed=embed)

            # Level-Rolle vergeben
            role_id = self.db.get_role_for_level(guild_id, new_level)
            if role_id:
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await message.author.add_roles(role, reason=f"Level {new_level} erreicht")
                        role_embed = discord.Embed(
                            title="🏆 Neue Rolle erhalten!",
                            description=f"{message.author.mention} hat die Rolle **{role.name}** erhalten!",
                            color=0xffff00
                        )
                        role_embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                        await target_channel.send(embed=role_embed)
                    except discord.Forbidden:
                        # Log oder Nachricht an Admins falls Bot keine Berechtigung hat
                        pass

    @levelsystem.command(description="Zeigt das Server-Leaderboard mit Paginierung")
    async def leaderboard(self, ctx,
                          anzahl: discord.Option(int, "Anzahl der User", default=10, min_value=1, max_value=50)):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed)
            return

        leaderboard_data = self.db.get_leaderboard(ctx.guild.id, anzahl)

        if not leaderboard_data:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="Noch keine User im Leaderboard!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed)
            return

        embed = discord.Embed(
            title=f"📊 Leaderboard - Top {len(leaderboard_data)}",
            color=0x0099ff,
            timestamp=discord.utils.utcnow()
        )

        description = ""
        for i, (user_id, xp, level, messages, prestige) in enumerate(leaderboard_data, 1):
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"User {user_id}"

            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"**{i}.**"

            prestige_text = f"⭐{prestige} " if prestige > 0 else ""
            description += f"{medal} {prestige_text}**{username}** - Level {level} ({xp:,} XP)\n"

        embed.description = description
        embed.set_footer(text=f"Server: {ctx.guild.name}")

        await ctx.respond(embed=embed)

    @levelsystem.command(description="Zeigt erweiterte Benutzerstatistiken")
    async def profil(self, ctx,
                     user: discord.Option(discord.Member, "User dessen Profil angezeigt werden soll", default=None)):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed)
            return

        target_user = user or ctx.author
        user_stats = self.db.get_user_stats(target_user.id, ctx.guild.id)

        if not user_stats:
            embed = discord.Embed(
                title="❌ Kein Profil gefunden",
                description=f"{target_user.display_name} hat noch keine XP gesammelt!",
                color=0xff0000
            )
            await ctx.respond(embed=embed)
            return

        xp, level, messages, xp_needed, prestige, total_earned = user_stats
        rank = self.db.get_user_rank(target_user.id, ctx.guild.id)

        embed = discord.Embed(
            title=f"📊 Profil von {target_user.display_name}",
            color=target_user.color or 0x0099ff,
            timestamp=discord.utils.utcnow()
        )

        # Erste Zeile
        embed.add_field(name="🏆 Level", value=str(level), inline=True)
        embed.add_field(name="⭐ XP", value=f"{xp:,}", inline=True)
        embed.add_field(name="📈 Rang", value=f"#{rank}", inline=True)

        # Zweite Zeile  
        embed.add_field(name="💬 Nachrichten", value=f"{messages:,}", inline=True)
        embed.add_field(name="🎯 XP bis nächstes Level", value=f"{xp_needed:,}", inline=True)
        
        if prestige > 0:
            embed.add_field(name="✨ Prestige", value=f"⭐{prestige}", inline=True)

        # Dritte Zeile
        embed.add_field(name="💰 Gesamt verdiente XP", value=f"{total_earned:,}", inline=True)

        # XP pro Nachricht berechnen
        xp_per_msg = total_earned / messages if messages > 0 else 0
        embed.add_field(name="📊 Ø XP/Nachricht", value=f"{xp_per_msg:.1f}", inline=True)

        # Aktiver XP-Multiplikator
        multiplier = self.db.get_active_xp_multiplier(ctx.guild.id, target_user.id)
        if multiplier > 1.0:
            embed.add_field(name="🚀 Aktiver Boost", value=f"{multiplier}x", inline=True)

        # Fortschrittsbalken
        current_level_xp = xp - self.db.xp_for_level(level)
        next_level_xp = self.db.xp_for_level(level + 1) - self.db.xp_for_level(level)
        progress = current_level_xp / next_level_xp if next_level_xp > 0 else 1

        progress_bar = "█" * int(progress * 15) + "░" * (15 - int(progress * 15))
        embed.add_field(
            name="📊 Level-Fortschritt", 
            value=f"`{progress_bar}` {progress * 100:.1f}%\n`{current_level_xp:,} / {next_level_xp:,} XP`", 
            inline=False
        )

        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
        embed.set_footer(text=f"Server: {ctx.guild.name}")

        await ctx.respond(embed=embed)

    @levelsystem.command(description="Führt ein Prestige durch (Level 50+)")
    async def prestige(self, ctx):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        config = self.db.get_guild_config(ctx.guild.id)
        if not config.get('prestige_enabled', True):
            embed = discord.Embed(
                title="❌ Prestige deaktiviert",
                description="Das Prestige-System ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        user_stats = self.db.get_user_stats(ctx.author.id, ctx.guild.id)
        min_level = config.get('prestige_min_level', 50)
        
        if not user_stats or user_stats[1] < min_level:
            embed = discord.Embed(
                title="❌ Prestige nicht verfügbar",
                description=f"Du musst mindestens Level {min_level} erreichen!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Bestätigung erforderlich
        view = PrestigeConfirmView(self.db, ctx.author, ctx.guild)
        embed = discord.Embed(
            title="⚠️ Prestige Bestätigung",
            description=f"Möchtest du wirklich dein Level zurücksetzen?\n\n**Was passiert:**\n• Dein Level wird auf 0 zurückgesetzt\n• Deine XP werden auf 0 zurückgesetzt\n• Du erhältst einen Prestige-Rang (⭐)\n• Du behältst deine Nachrichten-Anzahl\n\n**Aktuelles Level:** {user_stats[1]}",
            color=0xffff00
        )
        embed.set_footer(text="Diese Aktion kann nicht rückgängig gemacht werden!")
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @levelsystem.command(description="Zeigt erweiterte Server-Analytics")
    async def analytics(self, ctx):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        analytics = self.db.get_detailed_analytics(ctx.guild.id)

        embed = discord.Embed(
            title="📊 Server Analytics",
            color=0x0099ff,
            timestamp=discord.utils.utcnow()
        )

        # Grundlegende Statistiken
        embed.add_field(name="👥 Aktive User", value=f"{analytics['total_users']:,}", inline=True)
        embed.add_field(name="📈 Durchschnittslevel", value=f"{analytics['avg_level']:.1f}", inline=True)
        embed.add_field(name="🏆 Höchstes Level", value=f"{analytics['max_level']}", inline=True)

        embed.add_field(name="⚡ Gesamt XP", value=f"{analytics['total_xp']:,}", inline=True)
        embed.add_field(name="💬 Gesamt Nachrichten", value=f"{analytics['total_messages']:,}", inline=True)
        embed.add_field(name="🕒 Heute aktiv", value=f"{analytics['active_today']}", inline=True)

        # Level-Verteilung
        distribution = analytics['level_distribution']
        embed.add_field(
            name="📊 Level-Verteilung",
            value=f"🌱 Anfänger (1-10): {distribution['novice']}\n"
                  f"📚 Fortgeschrittene (11-25): {distribution['intermediate']}\n"
                  f"🎯 Experten (26-50): {distribution['advanced']}\n"
                  f"👑 Meister (50+): {distribution['expert']}",
            inline=False
        )

        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Exportiert Leveldaten als CSV")
    @commands.has_permissions(administrator=True)
    async def export_data(self, ctx):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        data = self.db.export_guild_data(ctx.guild.id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['User ID', 'Username', 'Level', 'XP', 'Messages', 'Prestige', 'Total XP Earned'])

        for row in data:
            user_id, xp, level, messages, prestige, total_earned = row
            user = self.bot.get_user(user_id)
            username = user.display_name if user else "Unbekannt"
            writer.writerow([user_id, username, level, xp, messages, prestige, total_earned])

        file_content = output.getvalue().encode('utf-8')
        file = discord.File(io.BytesIO(file_content), filename=f"leveldata_{ctx.guild.id}_{int(time.time())}.csv")

        embed = discord.Embed(
            title="✅ Datenexport erfolgreich",
            description=f"Daten von {len(data)} Usern exportiert.",
            color=0x00ff00
        )

        await ctx.followup.send(embed=embed, file=file)

    # Level-Rollen Commands
    @levelrole.command(description="Fügt eine Level-Rolle hinzu")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, 
                  level: discord.Option(int, "Level für die Rolle", min_value=1),
                  rolle: discord.Option(discord.Role, "Die Rolle die vergeben werden soll"),
                  temporaer: discord.Option(bool, "Temporäre Rolle", default=False),
                  dauer_stunden: discord.Option(int, "Dauer in Stunden (nur bei temporären Rollen)", default=0)):
        
        if rolle.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Keine Berechtigung",
                description="Du kannst keine Rolle hinzufügen, die höher oder gleich deiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if rolle.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title="❌ Bot-Berechtigung fehlt",
                description="Ich kann diese Rolle nicht vergeben, da sie höher oder gleich meiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if temporaer and dauer_stunden <= 0:
            embed = discord.Embed(
                title="❌ Ungültige Dauer",
                description="Temporäre Rollen benötigen eine Dauer > 0 Stunden!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.add_level_role(ctx.guild.id, level, rolle.id, temporaer, dauer_stunden)

        temp_text = f" (temporär für {dauer_stunden}h)" if temporaer else ""
        embed = discord.Embed(
            title="✅ Level-Rolle hinzugefügt",
            description=f"Die Rolle **{rolle.name}** wird nun bei **Level {level}**{temp_text} vergeben!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelrole.command(description="Fügt mehrere Rollen für ein Level hinzu")
    @commands.has_permissions(manage_roles=True)
    async def add_multiple(self, ctx, level: int, *roles: discord.Role):
        if not roles:
            await ctx.respond("Du musst mindestens eine Rolle angeben!", ephemeral=True)
            return
        
        added_roles = []
        failed_roles = []
        
        for role in roles:
            if role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
                failed_roles.append(f"{role.name} (keine Berechtigung)")
                continue
            
            if role.position >= ctx.guild.me.top_role.position:
                failed_roles.append(f"{role.name} (Bot-Berechtigung fehlt)")
                continue
            
            self.db.add_level_role(ctx.guild.id, level, role.id)
            added_roles.append(role.name)
        
        embed = discord.Embed(color=0x00ff00 if added_roles else 0xff0000)
        
        if added_roles:
            embed.title = "✅ Level-Rollen hinzugefügt"
            embed.description = f"**Level {level}:** {', '.join(added_roles)}"
        
        if failed_roles:
            if added_roles:
                embed.add_field(name="❌ Fehlgeschlagen", value='\n'.join(failed_roles), inline=False)
            else:
                embed.title = "❌ Keine Rollen hinzugefügt"
                embed.description = '\n'.join(failed_roles)
        
        await ctx.respond(embed=embed)

    @levelrole.command(description="Bearbeitet eine bestehende Level-Rolle")
    @commands.has_permissions(manage_roles=True)
    async def edit(self, ctx, 
                   level: discord.Option(int, "Level der zu bearbeitenden Rolle", min_value=1),
                   neue_rolle: discord.Option(discord.Role, "Die neue Rolle")):
        # Prüfen ob Level-Rolle existiert
        level_roles = self.db.get_level_roles(ctx.guild.id)
        if not any(l == level for l, r, t, d in level_roles):
            embed = discord.Embed(
                title="❌ Level-Rolle nicht gefunden",
                description=f"Für Level {level} ist keine Rolle konfiguriert!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if neue_rolle.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Keine Berechtigung",
                description="Du kannst keine Rolle setzen, die höher oder gleich deiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if neue_rolle.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title="❌ Bot-Berechtigung fehlt",
                description="Ich kann diese Rolle nicht vergeben, da sie höher oder gleich meiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.add_level_role(ctx.guild.id, level, neue_rolle.id)

        embed = discord.Embed(
            title="✅ Level-Rolle bearbeitet",
            description=f"Die Rolle für **Level {level}** wurde zu **{neue_rolle.name}** geändert!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelrole.command(description="Entfernt eine Level-Rolle")
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx, level: discord.Option(int, "Level der zu entfernenden Rolle", min_value=1)):
        # Prüfen ob Level-Rolle existiert
        level_roles = self.db.get_level_roles(ctx.guild.id)
        if not any(l == level for l, r, t, d in level_roles):
            embed = discord.Embed(
                title="❌ Level-Rolle nicht gefunden",
                description=f"Für Level {level} ist keine Rolle konfiguriert!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.remove_level_role(ctx.guild.id, level)

        embed = discord.Embed(
            title="✅ Level-Rolle entfernt",
            description=f"Die Level-Rolle für **Level {level}** wurde entfernt!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelrole.command(description="Zeigt alle konfigurierten Level-Rollen")
    async def list(self, ctx):
        level_roles = self.db.get_level_roles(ctx.guild.id)

        if not level_roles:
            embed = discord.Embed(
                title="📝 Level-Rollen",
                description="Keine Level-Rollen konfiguriert!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed)
            return

        embed = discord.Embed(
            title="📝 Level-Rollen",
            color=0x0099ff,
            timestamp=discord.utils.utcnow()
        )

        description = ""
        for level, role_id, is_temp, duration in level_roles:
            role = ctx.guild.get_role(role_id)
            role_name = role.name if role else f"Gelöschte Rolle ({role_id})"
            
            temp_text = f" ⏰({duration}h)" if is_temp else ""
            description += f"**Level {level}:** {role_name}{temp_text}\n"

        embed.description = description
        embed.set_footer(text=f"Server: {ctx.guild.name}")

        await ctx.respond(embed=embed)

    # XP-Boost Commands
    @xpboost.command(description="Fügt einen globalen XP-Boost hinzu")
    @commands.has_permissions(manage_guild=True)
    async def add_global(self, ctx,
                         multiplier: discord.Option(float, "XP-Multiplikator", min_value=1.1, max_value=5.0),
                         dauer_stunden: discord.Option(int, "Dauer in Stunden", min_value=1, max_value=168)):
        
        self.db.add_xp_boost(ctx.guild.id, None, multiplier, dauer_stunden)
        
        embed = discord.Embed(
            title="🚀 Globaler XP-Boost aktiviert",
            description=f"**{multiplier}x** XP-Multiplikator für **{dauer_stunden} Stunden**\n"
                       f"Alle Server-Mitglieder erhalten mehr XP!",
            color=0x00ff00
        )
        embed.set_footer(text="Der Boost ist sofort aktiv!")
        await ctx.respond(embed=embed)

    @xpboost.command(description="Fügt einen persönlichen XP-Boost hinzu")
    @commands.has_permissions(manage_guild=True)
    async def add_user(self, ctx,
                       user: discord.Option(discord.Member, "Benutzer für den Boost"),
                       multiplier: discord.Option(float, "XP-Multiplikator", min_value=1.1, max_value=5.0),
                       dauer_stunden: discord.Option(int, "Dauer in Stunden", min_value=1, max_value=168)):
        
        self.db.add_xp_boost(ctx.guild.id, user.id, multiplier, dauer_stunden)
        
        embed = discord.Embed(
            title="🚀 Persönlicher XP-Boost aktiviert",
            description=f"**{user.mention}** erhält **{multiplier}x** XP für **{dauer_stunden} Stunden**!",
            color=0x00ff00
        )
        embed.set_footer(text="Der Boost ist sofort aktiv!")
        await ctx.respond(embed=embed)

    # Konfiguration Commands
    @levelconfig.command(description="Konfiguriert XP-Einstellungen")
    @commands.has_permissions(manage_guild=True)
    async def xp_settings(self, ctx,
                          min_xp: discord.Option(int, "Minimum XP pro Nachricht", default=None, min_value=1, max_value=50),
                          max_xp: discord.Option(int, "Maximum XP pro Nachricht", default=None, min_value=1, max_value=100),
                          cooldown: discord.Option(int, "Cooldown in Sekunden", default=None, min_value=5, max_value=300)):
        
        config_updates = {}
        if min_xp is not None:
            config_updates['min_xp'] = min_xp
        if max_xp is not None:
            config_updates['max_xp'] = max_xp
        if cooldown is not None:
            config_updates['xp_cooldown'] = cooldown
        
        if max_xp and min_xp and max_xp < min_xp:
            await ctx.respond("❌ Maximum XP kann nicht kleiner als Minimum XP sein!", ephemeral=True)
            return
        
        if not config_updates:
            await ctx.respond("❌ Du musst mindestens einen Wert ändern!", ephemeral=True)
            return
        
        self.db.set_guild_config(ctx.guild.id, **config_updates)
        
        current_config = self.db.get_guild_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="✅ XP-Einstellungen aktualisiert",
            color=0x00ff00
        )
        
        embed.add_field(name="💰 XP-Bereich", value=f"{current_config['min_xp']}-{current_config['max_xp']}", inline=True)
        embed.add_field(name="⏱️ Cooldown", value=f"{current_config['xp_cooldown']}s", inline=True)
        
        await ctx.respond(embed=embed)

    @levelconfig.command(description="Setzt XP-Multiplikator für einen Kanal")
    @commands.has_permissions(manage_guild=True)
    async def channel_multiplier(self, ctx,
                                channel: discord.Option(discord.TextChannel, "Kanal"),
                                multiplier: discord.Option(float, "Multiplikator (0.0 = keine XP)", min_value=0.0, max_value=5.0)):
        
        self.db.set_channel_multiplier(ctx.guild.id, channel.id, multiplier)
        
        if multiplier == 0:
            description = f"{channel.mention} gibt keine XP mehr."
            color = 0xff0000
        else:
            description = f"{channel.mention} hat **{multiplier}x** XP-Multiplikator."
            color = 0x00ff00
        
        embed = discord.Embed(
            title="✅ Kanal-Multiplikator gesetzt",
            description=description,
            color=color
        )
        await ctx.respond(embed=embed)

    @levelconfig.command(description="Fügt einen Kanal zur XP-Blacklist hinzu")
    @commands.has_permissions(manage_guild=True)
    async def blacklist_channel(self, ctx,
                               channel: discord.Option(discord.TextChannel, "Kanal zum Ausschließen")):
        
        self.db.add_blacklisted_channel(ctx.guild.id, channel.id)
        
        embed = discord.Embed(
            title="✅ Kanal ausgeschlossen",
            description=f"{channel.mention} wurde vom Levelsystem ausgeschlossen.",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelconfig.command(description="Setzt den Level-Up Nachrichten-Kanal")
    @commands.has_permissions(manage_guild=True)
    async def levelup_channel(self, ctx,
                             channel: discord.Option(discord.TextChannel, "Kanal für Level-Up Nachrichten", default=None)):
        
        if channel:
            self.db.set_guild_config(ctx.guild.id, level_up_channel=channel.id)
            embed = discord.Embed(
                title="✅ Level-Up Kanal gesetzt",
                description=f"Level-Up Nachrichten werden in {channel.mention} gesendet.",
                color=0x00ff00
            )
        else:
            self.db.set_guild_config(ctx.guild.id, level_up_channel=None)
            embed = discord.Embed(
                title="✅ Level-Up Kanal zurückgesetzt",
                description="Level-Up Nachrichten werden wieder im ursprünglichen Kanal gesendet.",
                color=0x00ff00
            )
        
        await ctx.respond(embed=embed)

    @levelconfig.command(description="Konfiguriert Prestige-Einstellungen")
    @commands.has_permissions(manage_guild=True)
    async def prestige_settings(self, ctx,
                               aktiviert: discord.Option(bool, "Prestige-System aktivieren/deaktivieren"),
                               min_level: discord.Option(int, "Minimum Level für Prestige", default=50, min_value=10, max_value=200)):
        
        self.db.set_guild_config(ctx.guild.id, prestige_enabled=aktiviert, prestige_min_level=min_level)
        
        embed = discord.Embed(
            title="✅ Prestige-Einstellungen aktualisiert",
            color=0x00ff00
        )
        
        status = "aktiviert" if aktiviert else "deaktiviert"
        embed.add_field(name="✨ Status", value=status.title(), inline=True)
        if aktiviert:
            embed.add_field(name="🎯 Minimum Level", value=str(min_level), inline=True)
        
        await ctx.respond(embed=embed)

    # System Commands
    @levelsystem.command(description="Aktiviert das Levelsystem")
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        if self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="ℹ️ Bereits aktiviert",
                description="Das Levelsystem ist bereits aktiviert!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.set_levelsystem_enabled(ctx.guild.id, True)

        embed = discord.Embed(
            title="✅ Levelsystem aktiviert",
            description="Das Levelsystem wurde erfolgreich aktiviert!\n\nBenutze `/levelconfig` um weitere Einstellungen vorzunehmen.",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Deaktiviert das Levelsystem")
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="ℹ️ Bereits deaktiviert",
                description="Das Levelsystem ist bereits deaktiviert!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.set_levelsystem_enabled(ctx.guild.id, False)

        embed = discord.Embed(
            title="✅ Levelsystem deaktiviert",
            description="Das Levelsystem wurde erfolgreich deaktiviert!\n\n*Hinweis: Alle Daten bleiben erhalten und können bei Reaktivierung wiederhergestellt werden.*",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Zeigt den detaillierten Status des Levelsystems")
    async def status(self, ctx):
        enabled = self.db.is_levelsystem_enabled(ctx.guild.id)
        config = self.db.get_guild_config(ctx.guild.id)

        embed = discord.Embed(
            title="📊 Levelsystem Status",
            description=f"Das Levelsystem ist **{'aktiviert' if enabled else 'deaktiviert'}**",
            color=0x00ff00 if enabled else 0xff0000,
            timestamp=discord.utils.utcnow()
        )

        if enabled:
            # Grundkonfiguration
            embed.add_field(
                name="⚙️ Konfiguration",
                value=f"**XP-Bereich:** {config['min_xp']}-{config['max_xp']}\n"
                      f"**Cooldown:** {config['xp_cooldown']}s\n"
                      f"**Prestige:** {'✅' if config['prestige_enabled'] else '❌'} (Level {config['prestige_min_level']}+)",
                inline=True
            )

            # Statistiken
            leaderboard = self.db.get_leaderboard(ctx.guild.id, 1)
            level_roles = self.db.get_level_roles(ctx.guild.id)
            total_users = len(self.db.get_leaderboard(ctx.guild.id, 1000))

            embed.add_field(
                name="📈 Statistiken",
                value=f"**Aktive User:** {total_users:,}\n"
                      f"**Level-Rollen:** {len(level_roles)}\n"
                      f"**XP-Boosts:** Aktiv",
                inline=True
            )

            if leaderboard:
                top_user = self.bot.get_user(leaderboard[0][0])
                top_username = top_user.display_name if top_user else f"User {leaderboard[0][0]}"
                prestige_text = f"⭐{leaderboard[0][4]} " if leaderboard[0][4] > 0 else ""
                
                embed.add_field(
                    name="👑 Top User", 
                    value=f"{prestige_text}**{top_username}**\nLevel {leaderboard[0][2]} ({leaderboard[0][1]:,} XP)", 
                    inline=True
                )

            # Level-Up Kanal
            if config['level_up_channel']:
                channel = ctx.guild.get_channel(config['level_up_channel'])
                channel_text = channel.mention if channel else "Gelöschter Kanal"
            else:
                channel_text = "Standard (Nachrichtenkanal)"
            
            embed.add_field(name="📢 Level-Up Kanal", value=channel_text, inline=True)

        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await ctx.respond(embed=embed)

    # Admin Commands
    @levelsystem.command(description="Setzt das Level eines Users (Admin)")
    @commands.has_permissions(administrator=True)
    async def set_level(self, ctx,
                       user: discord.Option(discord.Member, "Benutzer"),
                       level: discord.Option(int, "Neues Level", min_value=0, max_value=1000)):
        
        required_xp = self.db.xp_for_level(level)
        
        # User in Datenbank erstellen/aktualisieren
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_levels (user_id, guild_id, xp, level, messages, last_message, total_xp_earned)
            VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT messages FROM user_levels WHERE user_id = ? AND guild_id = ?), 0),
                    ?, 
                    COALESCE((SELECT total_xp_earned FROM user_levels WHERE user_id = ? AND guild_id = ?), 0) + ?)
        ''', (user.id, ctx.guild.id, required_xp, level, user.id, ctx.guild.id, time.time(), user.id, ctx.guild.id, required_xp))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Level gesetzt",
            description=f"{user.mention} ist jetzt **Level {level}** ({required_xp:,} XP)",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Fügt einem User XP hinzu (Admin)")
    @commands.has_permissions(administrator=True)
    async def add_xp(self, ctx,
                    user: discord.Option(discord.Member, "Benutzer"),
                    xp_amount: discord.Option(int, "XP-Menge", min_value=1, max_value=100000)):
        
        level_up, new_level = self.db.add_xp(user.id, ctx.guild.id, xp_amount, "Admin XP Grant")
        
        embed = discord.Embed(
            title="✅ XP hinzugefügt",
            description=f"{user.mention} hat **{xp_amount:,} XP** erhalten!",
            color=0x00ff00
        )
        
        if level_up:
            embed.add_field(name="🎉 Level Up!", value=f"Neues Level: **{new_level}**", inline=False)
        
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Setzt die Nachrichten-Anzahl eines Users (Admin)")
    @commands.has_permissions(administrator=True)
    async def set_messages(self, ctx,
                          user: discord.Option(discord.Member, "Benutzer"),
                          messages: discord.Option(int, "Anzahl Nachrichten", min_value=0, max_value=1000000)):
        
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_levels SET messages = ? 
            WHERE user_id = ? AND guild_id = ?
        ''', (messages, user.id, ctx.guild.id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Nachrichten-Anzahl gesetzt",
            description=f"{user.mention} hat jetzt **{messages:,} Nachrichten**",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Löscht die Leveldaten eines Users (Admin)")
    @commands.has_permissions(administrator=True)
    async def reset_user(self, ctx,
                        user: discord.Option(discord.Member, "Benutzer zum Zurücksetzen")):
        
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_levels WHERE user_id = ? AND guild_id = ?', (user.id, ctx.guild.id))
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        if affected_rows > 0:
            embed = discord.Embed(
                title="✅ User zurückgesetzt",
                description=f"Alle Leveldaten von {user.mention} wurden gelöscht.",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Keine Daten gefunden",
                description=f"{user.mention} hat keine Leveldaten auf diesem Server.",
                color=0x0099ff
            )
        
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(LevelSystem(bot))