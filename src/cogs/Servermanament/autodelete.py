from src.DevTools import AutoDeleteDB
import discord
from discord.ext import tasks
from discord.commands import SlashCommandGroup, Option
import ezcord
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AutoDelete(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_task.start()
        self.processing_channels = set()  # Verhindert doppelte Verarbeitung

    autodelete = SlashCommandGroup("autodelete", "Automatische Nachrichtenlöschung")

    @autodelete.command(name="setup", description="Richtet AutoDelete für einen Kanal ein.")
    async def setup(self, ctx,
                    channel: Option(discord.TextChannel, "Kanal", required=True),
                    duration: Option(int, "Zeit in Sekunden (min: 60, max: 604800)", required=True),
                    exclude_pinned: Option(bool, "Angepinnte Nachrichten ausschließen", default=True),
                    exclude_bots: Option(bool, "Bot-Nachrichten ausschließen", default=False)):

        # Validierung
        if duration < 60:
            await ctx.respond("❌ Mindestdauer ist 60 Sekunden (1 Minute).", ephemeral=True)
            return
        if duration > 604800:
            await ctx.respond("❌ Maximaldauer ist 604800 Sekunden (7 Tage).", ephemeral=True)
            return

        # Permissions prüfen
        if not channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.respond("❌ Ich habe keine Berechtigung, Nachrichten in diesem Kanal zu löschen.", ephemeral=True)
            return

        db = AutoDeleteDB()
        db.add_autodelete(channel.id, duration, exclude_pinned, exclude_bots)

        duration_str = self._format_duration(duration)
        await ctx.respond(
            f"✅ AutoDelete für {channel.mention} wurde aktiviert!\n"
            f"📅 Dauer: {duration_str}\n"
            f"📌 Angepinnte Nachrichten: {'Ausgeschlossen' if exclude_pinned else 'Eingeschlossen'}\n"
            f"🤖 Bot-Nachrichten: {'Ausgeschlossen' if exclude_bots else 'Eingeschlossen'}",
            ephemeral=True
        )

    @autodelete.command(name="list", description="Zeigt alle aktiven AutoDelete-Kanäle.")
    async def list(self, ctx):
        db = AutoDeleteDB()
        channels = db.get_all()
        if not channels:
            await ctx.respond("❌ Keine AutoDelete-Kanäle gefunden.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🗑️ Aktive AutoDelete-Kanäle",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        for chan_id, duration, exclude_pinned, exclude_bots in channels:
            channel = self.bot.get_channel(chan_id)
            if channel:
                duration_str = self._format_duration(duration)
                settings = []
                if exclude_pinned:
                    settings.append("📌 Angepinnte ausgeschlossen")
                if exclude_bots:
                    settings.append("🤖 Bots ausgeschlossen")

                settings_str = "\n".join(settings) if settings else "Keine besonderen Einstellungen"

                embed.add_field(
                    name=f"#{channel.name}",
                    value=f"⏱️ {duration_str}\n{settings_str}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="❌ Unbekannter Kanal",
                    value=f"ID: {chan_id}\n⏱️ {self._format_duration(duration)}",
                    inline=True
                )

        await ctx.respond(embed=embed, ephemeral=True)

    @autodelete.command(name="remove", description="Entfernt AutoDelete von einem Kanal.")
    async def remove(self, ctx,
                     channel: Option(discord.TextChannel, "Kanal", required=True)):
        db = AutoDeleteDB()
        if db.get_autodelete(channel.id):
            db.remove_autodelete(channel.id)
            await ctx.respond(f"🗑️ AutoDelete für {channel.mention} wurde entfernt.", ephemeral=True)
        else:
            await ctx.respond(f"❌ AutoDelete war für {channel.mention} nicht aktiviert.", ephemeral=True)

    @autodelete.command(name="stats", description="Zeigt Statistiken für einen AutoDelete-Kanal.")
    async def stats(self, ctx,
                    channel: Option(discord.TextChannel, "Kanal", required=True)):
        db = AutoDeleteDB()
        config = db.get_autodelete_full(channel.id)
        if not config:
            await ctx.respond(f"❌ AutoDelete ist für {channel.mention} nicht aktiviert.", ephemeral=True)
            return

        duration, exclude_pinned, exclude_bots = config
        stats = db.get_stats(channel.id)

        embed = discord.Embed(
            title=f"📊 AutoDelete Statistiken - #{channel.name}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="⏱️ Löschzeit", value=self._format_duration(duration), inline=True)
        embed.add_field(name="📌 Angepinnte", value="Ausgeschlossen" if exclude_pinned else "Eingeschlossen",
                         inline=True)
        embed.add_field(name="🤖 Bots", value="Ausgeschlossen" if exclude_bots else "Eingeschlossen", inline=True)

        if stats:
            embed.add_field(name="🗑️ Gelöschte Nachrichten", value=str(stats['deleted_count']), inline=True)
            embed.add_field(name="❌ Fehler", value=str(stats['error_count']), inline=True)
            if stats['last_deletion']:
                embed.add_field(name="🕒 Letzte Löschung", value=f"<t:{int(stats['last_deletion'])}:R>", inline=True)

        await ctx.respond(embed=embed, ephemeral=True)

    @autodelete.command(name="test", description="Testet die AutoDelete-Funktion für einen Kanal.")
    async def test(self, ctx,
                    channel: Option(discord.TextChannel, "Kanal", required=True)):
        db = AutoDeleteDB()
        config = db.get_autodelete_full(channel.id)
        if not config:
            await ctx.respond(f"❌ AutoDelete ist für {channel.mention} nicht aktiviert.", ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            deleted_count = await self._process_channel_deletion(channel.id, test_mode=True)
            await ctx.followup.send(
                f"✅ Test erfolgreich!\n"
                f"📝 {deleted_count} Nachrichten würden gelöscht werden.",
                ephemeral=True
            )
        except Exception as e:
            await ctx.followup.send(f"❌ Test fehlgeschlagen: {str(e)}", ephemeral=True)

    @tasks.loop(seconds=30)  # Erhöht auf 30 Sekunden für bessere Performance
    async def delete_task(self):
        try:
            db = AutoDeleteDB()
            channels = db.get_all()

            # Verarbeite Kanäle parallel, aber begrenzt
            semaphore = asyncio.Semaphore(3)  # Max 3 Kanäle gleichzeitig
            tasks = []

            for chan_id, duration, exclude_pinned, exclude_bots in channels:
                if chan_id not in self.processing_channels:
                    task = self._process_channel_with_semaphore(semaphore, chan_id)
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Fehler im delete_task: {e}")

    async def _process_channel_with_semaphore(self, semaphore, channel_id):
        async with semaphore:
            await self._process_channel_deletion(channel_id)

    async def _process_channel_deletion(self, channel_id, test_mode=False):
        if channel_id in self.processing_channels and not test_mode:
            return 0

        if not test_mode:
            self.processing_channels.add(channel_id)

        try:
            db = AutoDeleteDB()
            config = db.get_autodelete_full(channel_id)
            if not config:
                return 0

            duration, exclude_pinned, exclude_bots = config

            # Zeitplan-Prüfung
            if not self._is_in_schedule(channel_id):
                return 0

            channel = self.bot.get_channel(channel_id)
            if not channel:
                return 0

            deleted_count = 0
            error_count = 0
            cutoff_time = datetime.utcnow() - timedelta(seconds=duration)

            try:
                messages_to_delete = []
                async for msg in channel.history(limit=200, oldest_first=True):
                    if msg.created_at >= cutoff_time:
                        break

                    # Filterlogik
                    if exclude_pinned and msg.pinned:
                        continue
                    if exclude_bots and msg.author.bot:
                        continue

                    # Whitelist-Prüfung
                    if self._check_whitelist(msg, channel_id):
                        continue

                    messages_to_delete.append(msg)

                    # Batch-Löschung für bessere Performance
                    if len(messages_to_delete) >= 10:
                        if not test_mode:
                            deleted, errors = await self._bulk_delete_messages(channel, messages_to_delete)
                            deleted_count += deleted
                            error_count += errors
                        else:
                            deleted_count += len(messages_to_delete)
                        messages_to_delete.clear()

                # Restliche Nachrichten löschen
                if messages_to_delete:
                    if not test_mode:
                        deleted, errors = await self._bulk_delete_messages(channel, messages_to_delete)
                        deleted_count += deleted
                        error_count += errors
                    else:
                        deleted_count += len(messages_to_delete)

                # Statistiken aktualisieren
                if not test_mode and (deleted_count > 0 or error_count > 0):
                    db.update_stats(channel_id, deleted_count, error_count)

            except discord.errors.Forbidden:
                logger.warning(f"Keine Berechtigung für Kanal {channel_id}")
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von Kanal {channel_id}: {e}")
                if not test_mode:
                    db.update_stats(channel_id, 0, 1)

            return deleted_count

        finally:
            if not test_mode:
                self.processing_channels.discard(channel_id)

    async def _bulk_delete_messages(self, channel, messages):
        deleted_count = 0
        error_count = 0

        # Trenne alte und neue Nachrichten (Discord API Limitation)
        old_messages = []
        new_messages = []
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)

        for msg in messages:
            if msg.created_at < two_weeks_ago:
                old_messages.append(msg)
            else:
                new_messages.append(msg)

        # Bulk delete für neue Nachrichten
        if new_messages:
            try:
                await channel.delete_messages(new_messages)
                deleted_count += len(new_messages)
            except Exception as e:
                logger.error(f"Bulk delete Fehler: {e}")

        return deleted_count, error_count

    # Platzhalter für fehlende Methoden, um den Code lauffähig zu machen
    def _format_duration(self, duration: int) -> str:
        """Formatiert die Dauer in eine lesbare Zeichenkette (z.B. '1 Stunde')."""
        if duration >= 86400 and duration % 86400 == 0:
            return f"{duration // 86400} Tage"
        if duration >= 3600 and duration % 3600 == 0:
            return f"{duration // 3600} Stunden"
        if duration >= 60 and duration % 60 == 0:
            return f"{duration // 60} Minuten"
        return f"{duration} Sekunden"
        
    def _is_in_schedule(self, channel_id: int) -> bool:
        """Platzhalter: Prüft, ob der Kanal gerade gelöscht werden soll (immer True im Platzhalter)."""
        # Da diese Methode in Ihrem Originalcode nicht definiert ist, aber aufgerufen wird, 
        # muss sie entweder in der DB/Config abrufbar sein oder als Platzhalter existieren.
        # Wir lassen sie hier True zurückgeben, um die Löschlogik nicht zu blockieren.
        return True
    
    def _check_whitelist(self, message: discord.Message, channel_id: int) -> bool:
        """Platzhalter: Prüft, ob die Nachricht von der Löschung ausgenommen ist (immer False im Platzhalter)."""
        return False
        
def setup(bot):
    bot.add_cog(AutoDelete(bot))