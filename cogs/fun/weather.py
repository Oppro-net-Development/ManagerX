# Copyright (c) 2025 OPPRO.NET Network
import requests
from DevTools.backend import discord, slash_command, ezcord
from DevTools.backend import WEATHER_API
import discord
from discord import slash_command
from discord.ui import Container
import ezcord
from DevTools import DEFLAUT_COLOR


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

        embed = discord.Embed(
            title=f"Wetter in {location['name']}, {location['country']}",
            description=f"Zeitzone: {location['tz_id']}\nLetzte Aktualisierung: {current['last_updated']}",
            color=DEFLAUT_COLOR
        )

        embed.add_field(name="🌡️ Temperatur", value=f"{current['temp_c']}°C", inline=True)
        embed.add_field(name="💧 Luftfeuchtigkeit", value=f"{current['humidity']}%", inline=True)
        embed.add_field(name="🌬️ Wind", value=f"{current['wind_kph']} km/h ({current['wind_dir']})", inline=True)
        embed.add_field(name="☁️ Zustand", value=current['condition']['text'], inline=False)
        embed.add_field(name="🌫️ Sichtweite", value=f"{current['vis_km']} km", inline=True)
        embed.add_field(name="🌡️ Luftdruck", value=f"{current['pressure_mb']} hPa", inline=True)
        embed.add_field(name="🌅 Sonnenauf-/untergang", value=f"{current.get('astro', {}).get('sunrise', 'N/A')} / {current.get('astro', {}).get('sunset', 'N/A')}", inline=False)

        embed.set_thumbnail(url="http:" + current['condition']['icon'])
        embed.set_footer(text="Weather data provided by WeatherAPI")

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
