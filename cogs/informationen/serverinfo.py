import discord
from discord.ext import commands
from discord import SlashCommandGroup, Option
import datetime
import asyncio
from typing import Optional
import logging


class ServerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    server = SlashCommandGroup("server", "Server-Informationen und -Statistiken")

    @server.command(description="Zeigt umfassende Discord-Server Informationen an")
    async def info(self, ctx):
        """Hauptbefehl für Server-Informationen mit detaillierter Übersicht"""
        guild = ctx.guild
        
        try:
            await ctx.defer()  # Mehr Zeit für komplexe Berechnungen
            
            # Erweiterte Mitglieder-Statistiken
            members = guild.members
            total_members = len(members)
            
            # Status-Statistiken
            status_counts = {
                'online': len([m for m in members if m.status == discord.Status.online]),
                'idle': len([m for m in members if m.status == discord.Status.idle]),
                'dnd': len([m for m in members if m.status == discord.Status.dnd]),
                'offline': len([m for m in members if m.status == discord.Status.offline])
            }
            
            bots = len([m for m in members if m.bot])
            humans = total_members - bots
            
            # Kanal-Statistiken
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            stage_channels = len(guild.stage_channels)
            forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
            categories = len(guild.categories)
            total_channels = len(guild.channels)
            
            # Rollen und Features
            roles = len(guild.roles) - 1  # Exclude @everyone
            emojis = len(guild.emojis)
            stickers = len(guild.stickers)
            
            # Boost-Informationen
            boost_count = guild.premium_subscription_count or 0
            boost_tier = guild.premium_tier
            boosters = len(guild.premium_subscribers) if guild.premium_subscribers else 0
            
            # Haupt-Embed erstellen
            embed = discord.Embed(
                title=f"📊 {guild.name}",
                description=guild.description or "*Keine Beschreibung verfügbar*",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            # Server-Icon und Banner
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            if guild.banner:
                embed.set_image(url=guild.banner.url)
            
            # Grundlegende Informationen
            created_timestamp = int(guild.created_at.timestamp())
            embed.add_field(
                name="ℹ️ Allgemeine Informationen", 
                value=f"👑 **Besitzer:** {guild.owner.mention}\n"
                      f"🆔 **ID:** `{guild.id}`\n"
                      f"📅 **Erstellt:** <t:{created_timestamp}:F> (<t:{created_timestamp}:R>)\n"
                      f"🌍 **Region:** {self._get_region_flag()} Automatisch", 
                inline=False
            )
            
            # Mitglieder-Statistiken
            online_total = status_counts['online'] + status_counts['idle'] + status_counts['dnd']
            embed.add_field(
                name="👥 Mitglieder", 
                value=f"**Gesamt:** {total_members:,}\n"
                      f"👤 **Menschen:** {humans:,}\n"
                      f"🤖 **Bots:** {bots:,}\n"
                      f"🟢 **Online:** {online_total:,}\n"
                      f"├ 🟢 Aktiv: {status_counts['online']:,}\n"
                      f"├ 🟡 Abwesend: {status_counts['idle']:,}\n"
                      f"├ 🔴 Beschäftigt: {status_counts['dnd']:,}\n"
                      f"└ ⚫ Offline: {status_counts['offline']:,}", 
                inline=True
            )
            
            # Kanal-Informationen
            embed.add_field(
                name="📺 Kanäle", 
                value=f"**Gesamt:** {total_channels}\n"
                      f"💬 **Text:** {text_channels}\n"
                      f"🔊 **Voice:** {voice_channels}\n"
                      f"🎭 **Stage:** {stage_channels}\n"
                      f"📋 **Forum:** {forum_channels}\n"
                      f"📁 **Kategorien:** {categories}", 
                inline=True
            )
            
            # Server-Features und Anpassungen
            embed.add_field(
                name="🎨 Anpassungen", 
                value=f"🏷️ **Rollen:** {roles}\n"
                      f"😀 **Emojis:** {emojis}/{guild.emoji_limit}\n"
                      f"🎃 **Sticker:** {stickers}\n"
                      f"📁 **Dateigröße:** {guild.filesize_limit // 1024 // 1024} MB", 
                inline=True
            )
            
            # Boost-Informationen
            boost_benefits = self._get_boost_benefits(boost_tier)
            embed.add_field(
                name="💎 Nitro Boosts", 
                value=f"🚀 **Level:** {boost_tier}/3\n"
                      f"⭐ **Boosts:** {boost_count}\n"
                      f"👑 **Booster:** {boosters}\n"
                      f"🎁 **Benefits:** {boost_benefits}", 
                inline=True
            )
            
            # Sicherheit und Moderation
            verification_emoji = {
                discord.VerificationLevel.none: "🟢",
                discord.VerificationLevel.low: "🟡", 
                discord.VerificationLevel.medium: "🟠",
                discord.VerificationLevel.high: "🔴",
                discord.VerificationLevel.highest: "🔴"
            }
            
            nsfw_level_names = {
                discord.NSFWLevel.default: "Standard",
                discord.NSFWLevel.explicit: "Explizit", 
                discord.NSFWLevel.safe: "Sicher",
                discord.NSFWLevel.age_restricted: "Altersbeschränkt"
            }
            
            embed.add_field(
                name="🛡️ Sicherheit & Moderation", 
                value=f"{verification_emoji.get(guild.verification_level, '❓')} **Verifikation:** {guild.verification_level.name.title()}\n"
                      f"🔒 **2FA:** {'✅ Aktiviert' if guild.mfa_level else '❌ Deaktiviert'}\n"
                      f"🔞 **NSFW Level:** {nsfw_level_names.get(guild.nsfw_level, 'Unbekannt')}\n"
                      f"📢 **System Channel:** {guild.system_channel.mention if guild.system_channel else 'Nicht gesetzt'}", 
                inline=True
            )
            
            # Server-Features
            features = self._format_guild_features(guild.features)
            if features:
                embed.add_field(name="✨ Premium Features", value=features, inline=False)
            
            # Zusätzliche Informationen falls vorhanden
            if guild.vanity_url:
                embed.add_field(name="🔗 Vanity URL", value=f"discord.gg/{guild.vanity_url}", inline=True)
            
            if guild.rules_channel:
                embed.add_field(name="📜 Regeln", value=guild.rules_channel.mention, inline=True)
                
            if guild.public_updates_channel:
                embed.add_field(name="📢 Updates", value=guild.public_updates_channel.mention, inline=True)
            
            embed.set_footer(
                text=f"Angefragt von {ctx.author.display_name}", 
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in server info command: {e}")
            await ctx.followup.send("❌ Ein Fehler ist aufgetreten beim Laden der Server-Informationen.", ephemeral=True)

    @server.command(description="Zeigt Top-Rollen des Servers an")
    async def roles(self, ctx, limit: Option(int, "Anzahl der anzuzeigenden Rollen (max 25)", min_value=1, max_value=25, default=15)):
        """Zeigt die höchsten Rollen des Servers mit Details"""
        try:
            guild = ctx.guild
            roles = sorted([role for role in guild.roles if role.name != "@everyone"], 
                          key=lambda x: x.position, reverse=True)
            
            if not roles:
                await ctx.respond("❌ Keine besonderen Rollen auf diesem Server gefunden.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🏷️ Top Rollen in {guild.name}",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            role_list = []
            for i, role in enumerate(roles[:limit], 1):
                member_count = len(role.members)
                permissions_count = sum(1 for perm, value in role.permissions if value)
                
                # Spezielle Rollen-Indikatoren
                indicators = []
                if role.permissions.administrator:
                    indicators.append("👑")
                if role.permissions.manage_guild:
                    indicators.append("⚙️")
                if role.permissions.ban_members or role.permissions.kick_members:
                    indicators.append("🔨")
                if role.managed:
                    indicators.append("🤖")
                if role.hoist:
                    indicators.append("📌")
                
                indicator_str = "".join(indicators)
                
                role_list.append(
                    f"`#{i:2d}` {role.mention} {indicator_str}\n"
                    f"     👥 {member_count} | 🔐 {permissions_count} Perms | Pos: {role.position}"
                )
            
            # Aufteilen in mehrere Fields falls nötig
            chunk_size = 8
            for i in range(0, len(role_list), chunk_size):
                chunk = role_list[i:i+chunk_size]
                field_name = f"Rollen {i+1}-{min(i+chunk_size, len(role_list))}" if len(role_list) > chunk_size else "Rollen"
                embed.add_field(name=field_name, value="\n".join(chunk), inline=False)
            
            embed.add_field(
                name="📊 Statistiken", 
                value=f"**Gesamt:** {len(guild.roles)-1} Rollen\n"
                      f"**Angezeigt:** {min(limit, len(roles))}\n"
                      f"**Legende:** 👑 Admin | ⚙️ Management | 🔨 Moderation | 🤖 Bot | 📌 Angeheftet", 
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in server roles command: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Laden der Rollen.", ephemeral=True)

    @server.command(description="Zeigt Kanal-Übersicht des Servers")
    async def channels(self, ctx):
        """Zeigt eine strukturierte Übersicht aller Kanäle"""
        try:
            guild = ctx.guild
            
            embed = discord.Embed(
                title=f"📺 Kanäle in {guild.name}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            # Kategorien und ihre Kanäle
            categories_processed = set()
            
            # Kanäle ohne Kategorie
            no_category = [ch for ch in guild.channels if ch.category is None and not isinstance(ch, discord.CategoryChannel)]
            if no_category:
                channel_list = []
                for ch in no_category:
                    channel_list.append(f"{self._get_channel_emoji(ch)} {ch.name}")
                
                if len("\n".join(channel_list)) <= 1024:
                    embed.add_field(
                        name="📁 Ohne Kategorie",
                        value="\n".join(channel_list) or "Keine",
                        inline=False
                    )
            
            # Kategorien mit ihren Kanälen
            for category in guild.categories[:10]:  # Limit für Embed-Größe
                if category in categories_processed:
                    continue
                    
                channel_list = []
                for ch in category.channels:
                    channel_list.append(f"{self._get_channel_emoji(ch)} {ch.name}")
                
                if channel_list and len("\n".join(channel_list)) <= 1024:
                    embed.add_field(
                        name=f"📁 {category.name} ({len(category.channels)})",
                        value="\n".join(channel_list),
                        inline=True
                    )
                    categories_processed.add(category)
            
            # Statistiken
            stats = (
                f"📊 **Gesamt:** {len(guild.channels)}\n"
                f"💬 **Text:** {len(guild.text_channels)}\n"
                f"🔊 **Voice:** {len(guild.voice_channels)}\n"
                f"🎭 **Stage:** {len(guild.stage_channels)}\n"
                f"📋 **Forum:** {len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])}\n"
                f"📁 **Kategorien:** {len(guild.categories)}"
            )
            
            embed.add_field(name="📈 Statistiken", value=stats, inline=True)
            
            if len(guild.categories) > 10:
                embed.set_footer(text=f"... und {len(guild.categories) - 10} weitere Kategorien")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in server channels command: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Laden der Kanal-Übersicht.", ephemeral=True)

    @server.command(description="Zeigt Emoji-Übersicht des Servers")
    async def emojis(self, ctx):
        """Zeigt alle Custom Emojis des Servers"""
        try:
            guild = ctx.guild
            emojis = guild.emojis
            
            if not emojis:
                embed = discord.Embed(
                    title="😔 Keine Custom Emojis",
                    description="Dieser Server hat keine benutzerdefinierten Emojis.",
                    color=discord.Color.orange()
                )
                await ctx.respond(embed=embed)
                return
            
            # Emojis nach Typ sortieren
            static_emojis = [e for e in emojis if not e.animated]
            animated_emojis = [e for e in emojis if e.animated]
            
            embed = discord.Embed(
                title=f"😀 Emojis in {guild.name}",
                description=f"**{len(static_emojis)}** statische • **{len(animated_emojis)}** animierte • **{len(emojis)}/{guild.emoji_limit}** gesamt",
                color=discord.Color.yellow(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            # Statische Emojis (max 25 pro Field)
            if static_emojis:
                emoji_chunks = [static_emojis[i:i+25] for i in range(0, len(static_emojis), 25)]
                for i, chunk in enumerate(emoji_chunks[:3]):  # Max 3 Chunks
                    emoji_display = "".join([str(emoji) for emoji in chunk])
                    field_name = f"📷 Statische Emojis" if i == 0 else f"📷 Statische Emojis (Teil {i+1})"
                    embed.add_field(name=field_name, value=emoji_display or "Keine", inline=False)
            
            # Animierte Emojis
            if animated_emojis:
                emoji_chunks = [animated_emojis[i:i+25] for i in range(0, len(animated_emojis), 25)]
                for i, chunk in enumerate(emoji_chunks[:2]):  # Max 2 Chunks für animierte
                    emoji_display = "".join([str(emoji) for emoji in chunk])
                    field_name = f"🎬 Animierte Emojis" if i == 0 else f"🎬 Animierte Emojis (Teil {i+1})"
                    embed.add_field(name=field_name, value=emoji_display or "Keine", inline=False)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in server emojis command: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Laden der Emojis.", ephemeral=True)

    @server.command(description="Zeigt Server-Boosts und Premium-Features")
    async def boosts(self, ctx):
        """Detaillierte Boost-Informationen"""
        try:
            guild = ctx.guild
            
            embed = discord.Embed(
                title=f"💎 Server Boosts - {guild.name}",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            boost_count = guild.premium_subscription_count or 0
            boost_tier = guild.premium_tier
            boosters = guild.premium_subscribers or []
            
            # Aktuelle Boost-Situation
            embed.add_field(
                name="📊 Aktuelle Situation",
                value=f"🚀 **Level:** {boost_tier}/3\n"
                      f"⭐ **Boosts:** {boost_count}\n"
                      f"👑 **Booster:** {len(boosters)}\n"
                      f"📈 **Progress:** {self._get_boost_progress(boost_count, boost_tier)}",
                inline=False
            )
            
            # Nächstes Level
            next_level_info = self._get_next_level_info(boost_count, boost_tier)
            if next_level_info:
                embed.add_field(name="🎯 Nächstes Level", value=next_level_info, inline=False)
            
            # Aktuelle Benefits
            benefits = self._get_detailed_boost_benefits(guild)
            embed.add_field(name="🎁 Aktuelle Benefits", value=benefits, inline=False)
            
            # Top Booster (falls vorhanden)
            if boosters:
                booster_list = [booster.mention for booster in boosters[:10]]
                embed.add_field(
                    name=f"👑 Booster ({len(boosters)})",
                    value=", ".join(booster_list) + ("..." if len(boosters) > 10 else ""),
                    inline=False
                )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in server boosts command: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Laden der Boost-Informationen.", ephemeral=True)

    def _get_channel_emoji(self, channel):
        """Gibt das passende Emoji für einen Kanal-Typ zurück"""
        if isinstance(channel, discord.TextChannel):
            return "💬"
        elif isinstance(channel, discord.VoiceChannel):
            return "🔊"
        elif isinstance(channel, discord.StageChannel):
            return "🎭"
        elif isinstance(channel, discord.ForumChannel):
            return "📋"
        elif isinstance(channel, discord.CategoryChannel):
            return "📁"
        else:
            return "📺"

    def _get_region_flag(self):
        """Gibt eine Flagge für die Region zurück (falls erwünscht)"""
        return "🌍"  # Globus für automatische Region

    def _get_boost_benefits(self, tier):
        """Gibt die Benefits für ein Boost-Level zurück"""
        benefits = {
            0: "Keine",
            1: "50 Emoji Slots, 128kb Audio",
            2: "150 Emoji Slots, 256kb Audio, Banner",
            3: "250 Emoji Slots, 384kb Audio, Vanity URL"
        }
        return benefits.get(tier, "Unbekannt")

    def _get_detailed_boost_benefits(self, guild):
        """Detaillierte Boost-Benefits für den aktuellen Server"""
        tier = guild.premium_tier
        
        benefits = [
            f"😀 **Emoji Slots:** {guild.emoji_limit}",
            f"📁 **Dateigröße:** {guild.filesize_limit // 1024 // 1024} MB",
            f"🎵 **Audio Qualität:** {64 * (2 ** tier)} kbps"
        ]
        
        if tier >= 2:
            benefits.extend([
                "🖼️ **Server Banner:** ✅",
                "🎨 **Server Icon Animation:** ✅"
            ])
        
        if tier >= 3:
            benefits.extend([
                "🔗 **Vanity URL:** ✅", 
                "📺 **Go Live 1080p:** ✅"
            ])
        
        return "\n".join(benefits)

    def _get_boost_progress(self, current_boosts, current_tier):
        """Zeigt den Progress zum nächsten Level"""
        requirements = {1: 2, 2: 7, 3: 14}
        
        if current_tier >= 3:
            return "✅ Max Level erreicht!"
        
        next_tier = current_tier + 1
        needed = requirements[next_tier]
        progress = min(current_boosts, needed)
        
        bar_length = 10
        filled = int((progress / needed) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"{bar} {progress}/{needed}"

    def _get_next_level_info(self, current_boosts, current_tier):
        """Informationen über das nächste Boost-Level"""
        if current_tier >= 3:
            return None
            
        requirements = {1: 2, 2: 7, 3: 14}
        next_tier = current_tier + 1
        needed = requirements[next_tier] - current_boosts
        
        if needed <= 0:
            return f"🎉 Level {next_tier} bereits erreicht!"
        
        benefits = {
            1: "50 Emoji Slots, bessere Audio-Qualität (128 kbps)",
            2: "150 Emoji Slots, Server Banner, noch bessere Audio (256 kbps)", 
            3: "250 Emoji Slots, Vanity URL, beste Audio-Qualität (384 kbps)"
        }
        
        return f"**Level {next_tier}**\nNoch {needed} Boost{'s' if needed != 1 else ''} benötigt\n{benefits[next_tier]}"

    def _format_guild_features(self, features):
        """Formatiert Guild-Features für die Anzeige"""
        if not features:
            return None
            
        feature_names = {
            'ANIMATED_ICON': '🎭 Animiertes Icon',
            'BANNER': '🖼️ Server Banner', 
            'COMMERCE': '🛒 Commerce',
            'COMMUNITY': '🏘️ Community Server',
            'DISCOVERABLE': '🔍 Auffindbar',
            'FEATURABLE': '⭐ Auszeichnungsfähig',
            'INVITE_SPLASH': '🌊 Invite Splash',
            'MEMBER_VERIFICATION_GATE_ENABLED': '🚪 Mitglieder-Verifizierung',
            'NEWS': '📰 News Channel',
            'PARTNERED': '🤝 Partner',
            'PREVIEW_ENABLED': '👀 Preview aktiviert',
            'PUBLIC_DISABLED': '🔒 Nicht öffentlich',
            'VANITY_URL': '🔗 Vanity URL',
            'VERIFIED': '✅ Verifiziert',
            'VIP_REGIONS': '🌟 VIP Regionen',
            'WELCOME_SCREEN_ENABLED': '👋 Willkommensbildschirm'
        }
        
        formatted_features = []
        for feature in features:
            display_name = feature_names.get(feature, feature.replace('_', ' ').title())
            formatted_features.append(display_name)
        
        return "\n".join(formatted_features) if formatted_features else None


def setup(bot):
    bot.add_cog(ServerInfoCog(bot))