# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord.ext import commands, tasks
from discord import SlashCommandGroup
import logging
from typing import Optional
from DevTools import StatsDB
import asyncio
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class EnhancedStatsCog(commands.Cog):
    """
    Enhanced Discord Cog for tracking user statistics with global level system.
    Provides comprehensive tracking of messages, voice activity, and user progression.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = StatsDB()
        self.cleanup_task.start()
        logger.info("Enhanced StatsCog initialized")

    stats = SlashCommandGroup("stats", "Statistiken")

    def cog_unload(self):
        """Called when the cog is unloaded."""
        self.cleanup_task.cancel()
        self.db.close()
        logger.info("Enhanced StatsCog unloaded")

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Daily cleanup of old data."""
        await self.db.cleanup_old_data(days=90)

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Enhanced StatsCog ready - Bot connected as {self.bot.user}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """Track voice channel activity with enhanced features."""
        if member.bot:
            return

        try:
            user_id = member.id
            guild_id = member.guild.id

            # User left a voice channel
            if before.channel and not after.channel:
                await self.db.end_voice_session(user_id, before.channel.id)
                logger.debug(f"User {member.display_name} left voice channel {before.channel.name}")

            # User joined a voice channel
            elif not before.channel and after.channel:
                await self.db.start_voice_session(user_id, guild_id, after.channel.id)
                logger.debug(f"User {member.display_name} joined voice channel {after.channel.name}")

            # User switched voice channels
            elif before.channel and after.channel and before.channel.id != after.channel.id:
                await self.db.end_voice_session(user_id, before.channel.id)
                await self.db.start_voice_session(user_id, guild_id, after.channel.id)
                logger.debug(f"User {member.display_name} switched from {before.channel.name} to {after.channel.name}")

        except Exception as e:
            logger.error(f"Error handling voice state update for {member.display_name}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Track messages with enhanced analysis."""
        if message.author.bot or not message.guild:
            return

        try:
            # Analyze message content
            word_count = len(message.content.split()) if message.content else 0
            has_attachment = len(message.attachments) > 0
            message_type = 'text'

            if message.attachments:
                message_type = 'attachment'
            elif message.embeds:
                message_type = 'embed'
            elif message.stickers:
                message_type = 'sticker'

            await self.db.log_message(
                user_id=message.author.id,
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                message_id=message.id,
                word_count=word_count,
                has_attachment=has_attachment,
                message_type=message_type
            )

            logger.debug(f"Logged enhanced message {message.id} from {message.author.display_name}")

        except Exception as e:
            logger.error(f"Error logging enhanced message from {message.author.display_name}: {e}")

    @stats.command(
        name="statsistics",
        description="Zeige deine Aktivitätsstatistiken an"
    )
    async def stats_command(
            self,
            ctx: discord.ApplicationContext,
            zeitraum: discord.Option(
                str,
                description="Zeitraum für die Statistiken",
                choices=["24h", "7d", "30d"],
                required=False,
                default="24h"
            ),
            user: discord.Option(
                discord.Member,
                description="Statistiken eines anderen Users anzeigen (optional)",
                required=False
            )
    ):
        """Enhanced stats command with more detailed information."""
        await ctx.defer()

        try:
            target_user = user if user else ctx.author
            time_periods = {
                "24h": (24, "24 Stunden"),
                "7d": (24 * 7, "7 Tagen"),
                "30d": (24 * 30, "30 Tagen")
            }

            hours, period_name = time_periods[zeitraum]

            # Get regular stats
            message_count, voice_minutes = await self.db.get_user_stats(
                target_user.id, hours, ctx.guild.id
            )

            # Get global user info
            global_info = await self.db.get_global_user_info(target_user.id)

            # Format voice time
            voice_hours = int(voice_minutes // 60)
            voice_mins = int(voice_minutes % 60)
            voice_time_str = f"{voice_hours}h {voice_mins}m" if voice_hours > 0 else f"{voice_mins}m"

            # Create main embed
            embed = discord.Embed(
                title=f"📊 {'Deine' if target_user == ctx.author else f'{target_user.display_name}s'} Statistiken",
                description=f"Aktivität der letzten {period_name}",
                color=discord.Color.blue()
            )

            # Local server stats
            embed.add_field(
                name="📅 Server Aktivität",
                value=f"💬 **{message_count}** Nachrichten\n🎤 **{voice_time_str}** Voice-Zeit",
                inline=True
            )

            # Global stats if available
            if global_info:
                level = global_info['level']
                xp_progress = global_info['xp_progress']
                xp_needed = global_info['xp_needed']
                progress_bar = self._create_progress_bar(xp_progress, xp_needed)

                embed.add_field(
                    name="🌍 Global Level",
                    value=f"**Level {level}** {self._get_level_emoji(level)}\n{progress_bar}\n`{int(xp_progress)}/{int(xp_needed)} XP`",
                    inline=True
                )

                # Global totals
                total_voice_hours = int(global_info['total_voice_minutes'] // 60)
                embed.add_field(
                    name="🏆 Global Totals",
                    value=f"📨 **{global_info['total_messages']:,}** Nachrichten\n"
                          f"🎤 **{total_voice_hours:,}** Stunden Voice\n"
                          f"🔥 **{global_info['daily_streak']}** Tage Streak",
                    inline=True
                )

            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Angefragt von {ctx.author.display_name}")

            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error executing enhanced stats command: {e}")
            error_embed = discord.Embed(
                title="❌ Fehler",
                description="Es gab einen Fehler beim Abrufen der Statistiken.",
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @stats.command(
        name="globalstats",
        description="Zeige deine globalen Level-Statistiken über alle Server an"
    )
    async def global_stats_command(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(
                discord.Member,
                description="Global Stats eines anderen Users anzeigen",
                required=False
            )
    ):
        """Show detailed global statistics and achievements."""
        await ctx.defer()

        try:
            target_user = user if user else ctx.author
            global_info = await self.db.get_global_user_info(target_user.id)

            if not global_info:
                embed = discord.Embed(
                    title="📊 Keine Daten",
                    description=f"{'Du hast' if target_user == ctx.author else f'{target_user.display_name} hat'} noch keine globalen Statistiken.",
                    color=discord.Color.orange()
                )
                await ctx.followup.send(embed=embed)
                return

            level = global_info['level']
            xp = global_info['xp']
            xp_progress = global_info['xp_progress']
            xp_needed = global_info['xp_needed']

            # Create embed
            embed = discord.Embed(
                title=f"🌍 {'Deine' if target_user == ctx.author else f'{target_user.display_name}s'} Globalen Stats",
                description=f"Level-System über alle Server",
                color=self._get_level_color(level)
            )

            # Level info
            progress_bar = self._create_progress_bar(xp_progress, xp_needed)
            level_emoji = self._get_level_emoji(level)

            embed.add_field(
                name=f"{level_emoji} Level & XP",
                value=f"**Level {level}**\n{progress_bar}\n`{int(xp_progress):,} / {int(xp_needed):,} XP`\n`Total: {int(xp):,} XP`",
                inline=False
            )

            # Activity stats
            total_voice_hours = int(global_info['total_voice_minutes'] // 60)
            days_since_joined = (datetime.now() - datetime.fromisoformat(global_info['first_seen'])).days + 1
            avg_messages_per_day = global_info['total_messages'] / days_since_joined

            embed.add_field(
                name="📈 Aktivitäts-Statistiken",
                value=f"📨 **{global_info['total_messages']:,}** Nachrichten gesamt\n"
                      f"🎤 **{total_voice_hours:,}** Stunden in Voice\n"
                      f"🏢 **{global_info['total_servers']}** Server aktiv\n"
                      f"📊 **{avg_messages_per_day:.1f}** Nachrichten/Tag",
                inline=True
            )

            # Streak info
            embed.add_field(
                name="🔥 Streak Statistiken",
                value=f"🔥 **{global_info['daily_streak']}** Tage aktuell\n"
                      f"🏆 **{global_info['best_streak']}** Tage Rekord\n"
                      f"📅 Dabei seit **{days_since_joined}** Tagen",
                inline=True
            )

            # Recent achievements
            achievements = global_info['achievements'][-3:]  # Last 3 achievements
            if achievements:
                achievement_text = "\n".join(
                    [f"{ach.get('icon', '🏆')} {ach.get('name', 'Unknown')}" for ach in achievements])
                embed.add_field(
                    name="🏆 Neueste Erfolge",
                    value=achievement_text,
                    inline=True
                )

            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Angefragt von {ctx.author.display_name} • Globales Level-System")

            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error executing global stats command: {e}")
            error_embed = discord.Embed(
                title="❌ Fehler",
                description="Es gab einen Fehler beim Abrufen der globalen Statistiken.",
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @stats.command(
        name="leaderboard",
        description="Zeige die Top-User Rangliste an"
    )
    async def leaderboard_command(
            self,
            ctx: discord.ApplicationContext,
            typ: discord.Option(
                str,
                description="Art der Rangliste",
                choices=["global", "server"],
                required=False,
                default="server"
            ),
            limit: discord.Option(
                int,
                description="Anzahl der angezeigten User (max 20)",
                min_value=5,
                max_value=20,
                required=False,
                default=10
            )
    ):
        """Show leaderboard for global or server stats."""
        await ctx.defer()

        try:
            if typ == "global":
                leaderboard_data = await self.db.get_leaderboard(limit)
                title = "🌍 Globale Rangliste"
                description = "Top User nach globalem Level & XP"
            else:
                leaderboard_data = await self.db.get_leaderboard(limit, ctx.guild.id)
                title = f"🏢 {ctx.guild.name} Rangliste"
                description = "Top User der letzten 30 Tage"

            if not leaderboard_data:
                embed = discord.Embed(
                    title="📊 Keine Daten",
                    description="Keine Ranglisten-Daten verfügbar.",
                    color=discord.Color.orange()
                )
                await ctx.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.gold()
            )

            leaderboard_text = ""
            for i, data in enumerate(leaderboard_data, 1):
                try:
                    user = self.bot.get_user(data[0])
                    username = user.display_name if user else "Unbekannter User"

                    # Position emoji
                    if i == 1:
                        pos_emoji = "🥇"
                    elif i == 2:
                        pos_emoji = "🥈"
                    elif i == 3:
                        pos_emoji = "🥉"
                    else:
                        pos_emoji = f"{i}."

                    if typ == "global":
                        # Global leaderboard format: user_id, level, xp, messages, voice
                        level, xp, messages, voice = data[1], data[2], data[3], data[4]
                        level_emoji = self._get_level_emoji(level)
                        leaderboard_text += f"{pos_emoji} **{username}** {level_emoji}\n"
                        leaderboard_text += f"    Level {level} • {int(xp):,} XP\n\n"
                    else:
                        # Server leaderboard format: user_id, messages, words
                        messages, words = data[1], data[2]
                        leaderboard_text += f"{pos_emoji} **{username}**\n"
                        leaderboard_text += f"    {messages:,} Nachrichten • {words:,} Wörter\n\n"

                except Exception as e:
                    logger.error(f"Error processing leaderboard entry: {e}")
                    continue

            if leaderboard_text:
                embed.description = leaderboard_text
            else:
                embed.description = "Fehler beim Laden der Rangliste."

            embed.set_footer(text=f"Angefragt von {ctx.author.display_name}")
            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error executing leaderboard command: {e}")
            error_embed = discord.Embed(
                title="❌ Fehler",
                description="Es gab einen Fehler beim Laden der Rangliste.",
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @stats.command(
        name="achievements",
        description="Zeige deine freigeschalteten Erfolge an"
    )
    async def achievements_command(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(
                discord.Member,
                description="Erfolge eines anderen Users anzeigen",
                required=False
            )
    ):
        """Show user achievements."""
        await ctx.defer()

        try:
            target_user = user if user else ctx.author
            global_info = await self.db.get_global_user_info(target_user.id)

            if not global_info:
                embed = discord.Embed(
                    title="🏆 Keine Erfolge",
                    description=f"{'Du hast' if target_user == ctx.author else f'{target_user.display_name} hat'} noch keine Erfolge freigeschaltet.",
                    color=discord.Color.orange()
                )
                await ctx.followup.send(embed=embed)
                return

            achievements = global_info.get('achievements', [])

            if not achievements:
                embed = discord.Embed(
                    title="🏆 Noch keine Erfolge",
                    description=f"{'Du hast' if target_user == ctx.author else f'{target_user.display_name} hat'} noch keine Erfolge freigeschaltet.\nWerde aktiver um Erfolge zu sammeln!",
                    color=discord.Color.blue()
                )
                await ctx.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"🏆 {'Deine' if target_user == ctx.author else f'{target_user.display_name}s'} Erfolge",
                description=f"**{len(achievements)}** Erfolge freigeschaltet",
                color=discord.Color.gold()
            )

            # Group achievements by category or show all
            achievement_text = ""
            for ach in achievements:
                icon = ach.get('icon', '🏆')
                name = ach.get('name', 'Unbekannter Erfolg')
                desc = ach.get('description', 'Keine Beschreibung')
                unlocked = ach.get('unlocked_at', 'Unbekannt')

                achievement_text += f"{icon} **{name}**\n"
                achievement_text += f"    {desc}\n"
                if unlocked != 'Unbekannt':
                    try:
                        unlock_date = datetime.fromisoformat(unlocked).strftime("%d.%m.%Y")
                        achievement_text += f"    Freigeschaltet: {unlock_date}\n"
                    except:
                        pass
                achievement_text += "\n"

            # Split into multiple fields if too long
            if len(achievement_text) > 1024:
                # Split achievements into chunks
                chunks = [achievements[i:i + 5] for i in range(0, len(achievements), 5)]
                for i, chunk in enumerate(chunks):
                    field_text = ""
                    for ach in chunk:
                        icon = ach.get('icon', '🏆')
                        name = ach.get('name', 'Unbekannter Erfolg')
                        field_text += f"{icon} **{name}**\n"

                    embed.add_field(
                        name=f"Erfolge {i * 5 + 1}-{min((i + 1) * 5, len(achievements))}",
                        value=field_text,
                        inline=True
                    )
            else:
                embed.description = achievement_text

            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Angefragt von {ctx.author.display_name}")

            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error executing achievements command: {e}")
            error_embed = discord.Embed(
                title="❌ Fehler",
                description="Es gab einen Fehler beim Laden der Erfolge.",
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @stats.command(
        name="stats_info",
        description="Informationen über das erweiterte Statistik-System"
    )
    async def stats_info_command(self, ctx: discord.ApplicationContext):
        """Provide information about the enhanced statistics system."""
        embed = discord.Embed(
            title="ℹ️ Erweitertes Statistik-System",
            description="Informationen über das Activity-Tracking & Level-System",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Was wird getrackt?",
            value="• **Server-spezifisch:** Nachrichten & Voice-Zeit\n"
                  "• **Global:** Level, XP, Gesamtaktivität\n"
                  "• **Erweitert:** Wortanzahl, Anhänge, Streaks",
            inline=False
        )

        embed.add_field(
            name="🌍 Globales Level-System",
            value="• **XP-Quellen:** Nachrichten (+1-6 XP), Voice-Chat (+0.5 XP/min)\n"
                  "• **Level:** Basiert auf Gesamt-XP über alle Server\n"
                  "• **Erfolge:** Automatisch für Meilensteine freigeschaltet",
            inline=False
        )

        embed.add_field(
            name="🏆 Verfügbare Kommandos",
            value="• `/stats` - Server Aktivitäts-Statistiken\n"
                  "• `/globalstats` - Globale Level & Erfolge\n"
                  "• `/leaderboard` - Ranglisten (global/server)\n"
                  "• `/achievements` - Freigeschaltete Erfolge",
            inline=False
        )

        embed.add_field(
            name="🔒 Datenschutz",
            value="• Nur Metadaten werden gespeichert (keine Inhalte)\n"
                  "• Automatische Bereinigung alter Daten nach 90 Tagen\n"
                  "• [Vollständige Datenschutzerklärung](https://medicopter117.github.io/ManagerX-Web/privacy.html)",
            inline=False
        )

        embed.set_footer(text="Das globale Level-System funktioniert serverübergreifend!")
        await ctx.respond(embed=embed, ephemeral=True)

    def _create_progress_bar(self, current: float, maximum: float, length: int = 10) -> str:
        """Create a visual progress bar."""
        if maximum <= 0:
            return "▓" * length

        filled = int((current / maximum) * length)
        bar = "▓" * filled + "░" * (length - filled)
        percentage = (current / maximum) * 100
        return f"{bar} {percentage:.1f}%"

    def _get_level_emoji(self, level: int) -> str:
        """Get emoji based on user level."""
        if level >= 100:
            return "👑"
        elif level >= 50:
            return "🏆"
        elif level >= 25:
            return "🏅"
        elif level >= 10:
            return "⭐"
        elif level >= 5:
            return "🌟"
        else:
            return "🔰"

    def _get_level_color(self, level: int) -> discord.Color:
        """Get embed color based on user level."""
        if level >= 100:
            return discord.Color.gold()
        elif level >= 50:
            return discord.Color.purple()
        elif level >= 25:
            return discord.Color.red()
        elif level >= 10:
            return discord.Color.orange()
        elif level >= 5:
            return discord.Color.green()
        else:
            return discord.Color.blue()


def setup(bot: commands.Bot):
    """Setup function to add the enhanced cog to the bot."""
    bot.add_cog(EnhancedStatsCog(bot))