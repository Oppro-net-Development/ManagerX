from FastCoding import TempVCDatabase
from FastCoding import discord, commands, option, slash_command, ezcord
from FastCoding import emoji_yes, emoji_no, emoji_settings, ERROR_TITLE, ERROR_COLOR, SUCCESS_COLOR, AUTHOR, FLOOTER

db = TempVCDatabase()


class TempVC(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="create", description="Erstelle ein VC-Erstellungssystem")
    @option("creator_channel", description="Channel, den Mitglieder betreten, um ihren VC zu erstellen",
            channel_types=[discord.ChannelType.voice])
    @option("category", description="Kategorie, in der die Temp-Channels erstellt werden",
            channel_types=[discord.ChannelType.category])
    async def tempvc_create(self, ctx: discord.ApplicationContext, creator_channel: discord.VoiceChannel,
                            category: discord.CategoryChannel):
        if not ctx.author.guild_permissions.administrator:
            # No permission embed
            no_perm_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            no_perm_embed.set_author(name=AUTHOR)
            no_perm_embed.add_field(name=f"{emoji_no} Keine Berechtigung", value="Du brauchst Administratorrechte.",
                                    inline=False)
            no_perm_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=no_perm_embed, ephemeral=True)

        try:
            db.set_tempvc_settings(ctx.guild.id, creator_channel.id, category.id)

            # Success embed
            success_embed = discord.Embed(
                title=f"{emoji_yes} Temp-VC System aktiviert",
                color=SUCCESS_COLOR,
                description="Das temporäre Voice-Channel System wurde erfolgreich eingerichtet!"
            )
            success_embed.set_author(name=AUTHOR)
            success_embed.add_field(name="🎤 Ersteller-Channel", value=creator_channel.mention, inline=True)
            success_embed.add_field(name="📁 Kategorie", value=category.mention, inline=True)
            success_embed.add_field(name="ℹ️ Information",
                                    value="Mitglieder können nun den Ersteller-Channel betreten, um automatisch einen eigenen temporären Voice-Channel zu erhalten.",
                                    inline=False)
            success_embed.set_footer(text=FLOOTER)

            await ctx.respond(embed=success_embed, ephemeral=True)
        except Exception as e:
            # Error embed
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            error_embed.set_author(name=AUTHOR)
            error_embed.add_field(name=f"{emoji_no} Fehler beim Erstellen", value=f"```{str(e)}```", inline=False)
            error_embed.set_footer(text=FLOOTER)
            await ctx.respond(embed=error_embed, ephemeral=True)

    @slash_command(name="remove", description="Entferne das VC-Erstellungssystem")
    async def tempvc_remove(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.administrator:
            # No permission embed
            no_perm_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            no_perm_embed.set_author(name=AUTHOR)
            no_perm_embed.add_field(name=f"{emoji_no} Keine Berechtigung", value="Du brauchst Administratorrechte.",
                                    inline=False)
            no_perm_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=no_perm_embed, ephemeral=True)

        try:
            settings = db.get_tempvc_settings(ctx.guild.id)
            if not settings:
                # No system active embed
                no_system_embed = discord.Embed(
                    title=f"{emoji_no} Kein System aktiv",
                    color=ERROR_COLOR,
                    description="Es ist derzeit kein Temp-VC System auf diesem Server aktiv."
                )
                no_system_embed.set_author(name=AUTHOR)
                no_system_embed.set_footer(text=FLOOTER)
                return await ctx.respond(embed=no_system_embed, ephemeral=True)

            db.remove_tempvc_settings(ctx.guild.id)

            # Success removal embed
            removal_embed = discord.Embed(
                title=f"{emoji_yes} System deaktiviert",
                color=SUCCESS_COLOR,
                description="Das Temp-VC System wurde erfolgreich deaktiviert!"
            )
            removal_embed.set_author(name=AUTHOR)
            removal_embed.add_field(name="ℹ️ Information",
                                    value="Bestehende temporäre Channels bleiben bestehen, aber es werden keine neuen mehr erstellt.",
                                    inline=False)
            removal_embed.set_footer(text=FLOOTER)

            await ctx.respond(embed=removal_embed, ephemeral=True)
        except Exception as e:
            # Error embed
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            error_embed.set_author(name=AUTHOR)
            error_embed.add_field(name=f"{emoji_no} Fehler beim Entfernen", value=f"```{str(e)}```", inline=False)
            error_embed.set_footer(text=FLOOTER)
            await ctx.respond(embed=error_embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if after.channel:
                await self.handle_creator_channel_join(member, after.channel)
            if before.channel:
                await self.handle_channel_leave(before.channel)
        except Exception as e:
            print(f"Error in voice state update: {e}")

    async def handle_creator_channel_join(self, member: discord.Member, channel: discord.VoiceChannel):
        settings = db.get_tempvc_settings(member.guild.id)
        if not settings:
            return

        creator_channel_id, category_id, auto_delete_time = settings

        if channel.id != creator_channel_id:
            return

        guild = member.guild
        category = discord.utils.get(guild.categories, id=category_id)
        if not category:
            print(f"Category with ID {category_id} not found in guild {guild.id}")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                manage_permissions=True
            )
        }

        try:
            temp_channel = await guild.create_voice_channel(
                name=f"🔊 {member.display_name}'s Raum",
                category=category,
                overwrites=overwrites
            )
            db.add_temp_channel(temp_channel.id, guild.id, member.id)
            await member.move_to(temp_channel)

        except discord.Forbidden:
            print(f"Missing permissions to create voice channel in guild {guild.id}")
        except discord.HTTPException as e:
            print(f"HTTP error when creating voice channel: {e}")
        except Exception as e:
            print(f"Unexpected error when creating temp channel: {e}")

    async def handle_channel_leave(self, channel: discord.VoiceChannel):
        if len(channel.members) > 0:
            return

        if not db.is_temp_channel(channel.id):
            return

        try:
            db.remove_temp_channel(channel.id)
            await channel.delete(reason="Temp channel cleanup - channel empty")

        except discord.Forbidden:
            print(f"Missing permissions to delete channel {channel.id}")
        except discord.NotFound:
            db.remove_temp_channel(channel.id)
        except Exception as e:
            print(f"Error deleting temp channel {channel.id}: {e}")

    @slash_command(name="settings", description="Zeige die aktuellen Temp-VC Einstellungen")
    async def tempvc_settings(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.administrator:
            # No permission embed
            no_perm_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            no_perm_embed.set_author(name=AUTHOR)
            no_perm_embed.add_field(name=f"{emoji_no} Keine Berechtigung", value="Du brauchst Administratorrechte.",
                                    inline=False)
            no_perm_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=no_perm_embed, ephemeral=True)

        settings = db.get_tempvc_settings(ctx.guild.id)
        if not settings:
            # No system active embed
            no_system_embed = discord.Embed(
                title=f"{emoji_no} Kein System aktiv",
                color=ERROR_COLOR,
                description="Es ist derzeit kein Temp-VC System auf diesem Server aktiv."
            )
            no_system_embed.set_author(name=AUTHOR)
            no_system_embed.add_field(name="💡 Tipp", value="Verwende `/create` um ein Temp-VC System einzurichten.",
                                      inline=False)
            no_system_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=no_system_embed, ephemeral=True)

        creator_channel_id, category_id, auto_delete_time = settings
        creator_channel = ctx.guild.get_channel(creator_channel_id)
        category = ctx.guild.get_channel(category_id)

        # Settings embed (enhanced version of existing one)
        embed = discord.Embed(
            title=f"{emoji_settings} Temp-VC Einstellungen",
            color=discord.Color.blue(),
            description="Aktuelle Konfiguration des temporären Voice-Channel Systems"
        )
        embed.set_author(name=AUTHOR)
        embed.add_field(
            name="🎤 Ersteller-Channel",
            value=creator_channel.mention if creator_channel else f"{emoji_no} Channel nicht gefunden (ID: {creator_channel_id})",
            inline=True
        )
        embed.add_field(
            name="📁 Kategorie",
            value=category.mention if category else f"{emoji_no} Kategorie nicht gefunden (ID: {category_id})",
            inline=True
        )
        embed.add_field(
            name="⏰ Auto-Löschzeit",
            value=f"{auto_delete_time} Minuten",
            inline=True
        )
        embed.add_field(
            name="ℹ️ Status",
            value=f"{emoji_yes} System aktiv" if creator_channel and category else f"{emoji_no} Fehlerhafte Konfiguration",
            inline=False
        )
        embed.set_footer(text=FLOOTER)

        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(TempVC(bot))