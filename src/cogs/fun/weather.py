# Copyright (c) 2025 OPPRO.NET Network
import requests
from src.DevTools.backend import discord, slash_command, ezcord
from src.DevTools.backend import WEATHER_API
import discord
from discord import slash_command
from discord.ui import Container
import ezcord


class Weather(ezcord.Cog, group="fun"):
    def __init__(self, bot: ezcord.Bot):
        self.bot = bot

    @slash_command(name="weather", description="Erhalte das Wetter für eine Stadt")
    async def weather(self, ctx: discord.ApplicationContext, city: str):
        """Get the weather for a city"""
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API}&q={city}&lang=de"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            await ctx.respond("⚠️ Es gab ein Problem beim Abrufen der Wetterdaten. Bitte versuche es später erneut.")
            return

        if "error" in data:
            await ctx.respond(f"⚠️ Fehler: {data['error']['message']}")
            return

        location = data['location']
        current = data['current']

        container = Container()
        container.add_text(
            f"## Wetter in {location['name']}, {location['country']} \n"
            f"**Zeitzone:** {location['tz_id']}\n**Letzte Aktualisierung:** {current['last_updated']}"
        )
        container.add_separator()
        container.add_text(
            
            f"**🌡️ Temperatur:** {current['temp_c']}°C \n"
            f"**💧 Luftfeuchtigkeit:** {current['humidity']}% \n"
            f"**🌬️ Wind:** {current['wind_kph']} km/h ({current['wind_dir']}) \n "
            f"**☁️ Zustand:** {current['condition']['text']} \n"
            f"**🌫️ Sichtweite:** {current['vis_km']} km \n"
            f"**🌡️ Luftdruck:** {current['pressure_mb']} hPa"
        )
        
        view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)

def setup(bot: ezcord.Bot):
    bot.add_cog(Weather(bot))
