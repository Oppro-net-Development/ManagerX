# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord.ext import commands
import logging
from typing import Optional
from FastCoding import StatsDB

logger = logging.getLogger(__name__)


class StatsCog(commands.Cog):
    """
    Discord Cog for tracking user statistics including voice chat time and message counts.
    Provides slash commands for users to view their activity statistics.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = StatsDB()
        logger.info("StatsCog initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"StatsCog ready - Bot connected as {self.bot.user}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """
        Track voice channel activity when users join, leave, or switch channels.

        Args:
            member: The Discord member whose voice state changed
            before: The voice state before the change
            after: The voice state after the change
        """
        # Ignore bot users
        if member.bot:
            return

        try:
            user_id = member.id

            # User left a voice channel
            if before.channel and not after.channel:
                await self.db.end_voice_session(user_id, before.channel.id)
                logger.debug(f"User {member.display_name} left voice channel {before.channel.name}")

            # User joined a voice channel
            elif not before.channel and after.channel:
                await self.db.start_voice_session(user_id, after.channel.id)
                logger.debug(f"User {member.display_name} joined voice channel {after.channel.name}")

            # User switched voice channels
            elif before.channel and after.channel and before.channel.id != after.channel.id:
                # End the previous session
                await self.db.end_voice_session(user_id, before.channel.id)
                # Start a new session in the new channel
                await self.db.start_voice_session(user_id, after.channel.id)
                logger.debug(f"User {member.display_name} switched from {before.channel.name} to {after.channel.name}")

            # Other voice state changes (mute, deafen, etc.) are ignored

        except Exception as e:
            logger.error(f"Error handling voice state update for {member.display_name}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Track messages sent by users (excluding bots).

        Args:
            message: The Discord message object
        """
        # Ignore messages from bots
        if message.author.bot:
            return

        # Ignore DM messages (only track guild messages)
        if not message.guild:
            return

        try:
            await self.db.log_message(
                user_id=message.author.id,
                channel_id=message.channel.id,
                message_id=message.id
            )
            logger.debug(f"Logged message {message.id} from {message.author.display_name}")

        except Exception as e:
            logger.error(f"Error logging message from {message.author.display_name}: {e}")

    @discord.slash_command(
        name="stats",
        description="Zeige deine Aktivitätsstatistiken für einen bestimmten Zeitraum an"
    )
    async def stats_command(
            self,
            ctx: discord.ApplicationContext,
            zeitraum: discord.Option(
                str,
                description="Zeitraum für die Statistiken",
                choices=["24h", "7d", "30d"],
                required=True
            )
    ):
        """
        Slash command to display user activity statistics.

        Args:
            ctx: The application context
            zeitraum: Time period for statistics ("24h", "7d", "30d")
        """
        await ctx.defer()  # Defer the response since database operations might take time

        try:
            # Convert time period to hours
            time_periods = {
                "24h": (24, "24 Stunden"),
                "7d": (24 * 7, "7 Tagen"),
                "30d": (24 * 30, "30 Tagen")
            }

            if zeitraum not in time_periods:
                embed = discord.Embed(
                    title="❌ Ungültiger Zeitraum",
                    description="Bitte wähle einen gültigen Zeitraum: `24h`, `7d` oder `30d`",
                    color=discord.Color.red()
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return

            hours, period_name = time_periods[zeitraum]
            user_id = ctx.author.id

            # Get user statistics from database
            message_count, voice_minutes = await self.db.get_user_stats(user_id, hours)

            # Format voice time
            voice_hours = int(voice_minutes // 60)
            voice_mins = int(voice_minutes % 60)

            if voice_hours > 0:
                voice_time_str = f"{voice_hours} Stunde{'n' if voice_hours != 1 else ''} {voice_mins} Minute{'n' if voice_mins != 1 else ''}"
            else:
                voice_time_str = f"{voice_mins} Minute{'n' if voice_mins != 1 else ''}"

            # Create embed response
            embed = discord.Embed(
                title=f"📊 Deine Aktivitätsstatistiken",
                description=f"Statistiken für die letzten {period_name}",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="💬 Nachrichten",
                value=f"{message_count} Nachricht{'en' if message_count != 1 else ''}",
                inline=True
            )

            embed.add_field(
                name="🎤 Voice-Chat Zeit",
                value=voice_time_str,
                inline=True
            )

            embed.set_footer(text=f"Angefragt von {ctx.author.display_name}")
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            await ctx.followup.send(embed=embed)
            logger.info(f"Stats command executed for {ctx.author.display_name} - Period: {zeitraum}")

        except Exception as e:
            logger.error(f"Error executing stats command for {ctx.author.display_name}: {e}")

            error_embed = discord.Embed(
                title="❌ Fehler",
                description="Es gab einen Fehler beim Abrufen deiner Statistiken. Bitte versuche es später erneut.",
                color=discord.Color.red()
            )

            try:
                await ctx.followup.send(embed=error_embed, ephemeral=True)
            except:
                # If followup fails, try to send a regular response
                try:
                    await ctx.respond(embed=error_embed, ephemeral=True)
                except:
                    logger.error("Failed to send error response to user")

    @discord.slash_command(
        name="stats_info",
        description="Informationen über das Statistik-System"
    )
    async def stats_info_command(self, ctx: discord.ApplicationContext):
        """
        Provide information about the statistics tracking system.

        Args:
            ctx: The application context
        """
        embed = discord.Embed(
            title="ℹ️ Statistik-System Info",
            description="Informationen über das Activity-Tracking",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📝 Was wird getrackt?",
            value="• Nachrichten in Text-Channels\n• Zeit in Voice-Channels\n• Channel-Wechsel werden berücksichtigt",
            inline=False
        )

        embed.add_field(
            name="⏰ Verfügbare Zeiträume",
            value="• `24h` - Letzte 24 Stunden\n• `7d` - Letzte 7 Tage\n• `30d` - Letzte 30 Tage",
            inline=False
        )

        embed.add_field(
            name="🔒 Datenschutz",
            value="• Nur deine eigenen Statistiken sind für dich sichtbar\n• Keine Nachrichten-Inhalte werden gespeichert\n• Nur Zeitstempel und Channel-IDs werden erfasst.\n Mehr in unserer [Datenschutzerklärung](https://medicopter117.github.io/ManagerX-Web/privacy.html)",
            inline=False
        )

        embed.set_footer(text="Nutze /stats [zeitraum] um deine Statistiken anzuzeigen")

        await ctx.respond(embed=embed, ephemeral=True)

    def cog_unload(self):
        """Called when the cog is unloaded."""
        logger.info("StatsCog unloaded")


def setup(bot: commands.Bot):
    """
    Setup function to add the cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    bot.add_cog(StatsCog(bot))