import discord
from discord.ext import commands
from discord import option
from DevTools import AutoRoleDatabase
from handler import TranslationHandler as TH

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AutoRoleDatabase()
    
    async def cog_load(self):
        """Wird aufgerufen, wenn der Cog geladen wird"""
        await self.db.init_db()
    
    autorole = discord.SlashCommandGroup(
        name="autorole",
        description="Verwalte das Autorole-System",
        default_member_permissions=discord.Permissions(administrator=True)
    )
    
    @autorole.command(name="add", description="Füge eine neue Autorole hinzu")
    @option(
        name="rolle",
        description="Die Rolle, die vergeben werden soll",
        type=discord.Role,
        required=True
    )
    async def autorole_add(self, ctx: discord.ApplicationContext, rolle: discord.Role):
        """Fügt eine neue Autorole hinzu"""
        
        # Prüfe, ob der Bot die Rolle vergeben kann
        if rolle.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.role_to_high.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.role_to_high.desc"),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if rolle.managed:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.role_managed.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.role_managed.desc"),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        # Füge die Autorole hinzu
        autorole_id = await self.db.add_autorole(ctx.guild.id, rolle.id)
        
        embed = discord.Embed(
            title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.add_success.title"),
            description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.add_success.desc", role=rolle.mention, autorole_id=autorole_id),
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)
    
    @autorole.command(name="remove", description="Entferne eine Autorole")
    @option(
        name="autorole_id",
        description="Die ID der Autorole (z.B. 26-25-153)",
        type=str,
        required=True
    )
    async def autorole_remove(self, ctx: discord.ApplicationContext, autorole_id: str):
        """Entfernt eine Autorole anhand der ID"""
        
        config = await self.db.get_autorole(autorole_id)
        
        if not config:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.not_found.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.not_found.desc", autorole_id=autorole_id),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if config["guild_id"] != ctx.guild.id:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.wrong_guild.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.wrong_guild.desc"),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        await self.db.remove_autorole(autorole_id)
        
        embed = discord.Embed(
            title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.remove_success.title"),
            description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.remove_success.desc", autorole_id=autorole_id),
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)
    
    @autorole.command(name="toggle", description="Aktiviere oder deaktiviere eine Autorole")
    @option(
        name="autorole_id",
        description="Die ID der Autorole (z.B. 26-25-153)",
        type=str,
        required=True
    )
    @option(
        name="status",
        description="Status der Autorole",
        type=str,
        choices=["aktivieren", "deaktivieren"],
        required=True
    )
    async def autorole_toggle(self, ctx: discord.ApplicationContext, autorole_id: str, status: str):
        """Aktiviert oder deaktiviert eine Autorole"""
        
        config = await self.db.get_autorole(autorole_id)
        
        if not config:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.not_found.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.not_found.desc", autorole_id=autorole_id),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if config["guild_id"] != ctx.guild.id:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.wrong_guild.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.wrong_guild.desc"),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        enabled = status == "aktivieren"
        await self.db.toggle_autorole(autorole_id, enabled)
        
        status_text = "enabled" if enabled else "disabled"
        embed = discord.Embed(
            title=await TH.get_for_user(self.bot, ctx.author.id, f"cog_autorole.messages.toggle_success.{status_text}_title"),
            description=await TH.get_for_user(self.bot, ctx.author.id, f"cog_autorole.messages.toggle_success.{status_text}_desc", autorole_id=autorole_id),
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)
    
    @autorole.command(name="list", description="Zeige alle Autoroles auf diesem Server")
    async def autorole_list(self, ctx: discord.ApplicationContext):
        """Zeigt alle Autoroles für den Server"""
        
        autoroles = await self.db.get_all_autoroles(ctx.guild.id)
        
        if not autoroles:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.no_roles.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.no_roles.desc"),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.list.title"),
            description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.list.desc", guild_name=ctx.guild.name),
            color=discord.Color.blue()
        )
        
        for ar in autoroles:
            role = ctx.guild.get_role(ar["role_id"])
            if role:
                status = "🟢 Aktiv" if ar["enabled"] else "🔴 Inaktiv"
                embed.add_field(
                    name=f"ID: `{ar['autorole_id']}`",
                    value=f"**Rolle:** {role.mention}\n**Status:** {status}\n**Mitglieder:** {len(role.members)}",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"ID: `{ar['autorole_id']}`",
                    value=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.list.role_deleted"),
                    inline=False
                )
        
        await ctx.respond(embed=embed)
    
    @autorole.command(name="info", description="Zeige Details zu einer spezifischen Autorole")
    @option(
        name="autorole_id",
        description="Die ID der Autorole (z.B. 26-25-153)",
        type=str,
        required=True
    )
    async def autorole_info(self, ctx: discord.ApplicationContext, autorole_id: str):
        """Zeigt Details zu einer spezifischen Autorole"""
        
        config = await self.db.get_autorole(autorole_id)
        
        if not config:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.not_found.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.not_found.desc", autorole_id=autorole_id),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if config["guild_id"] != ctx.guild.id:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.wrong_guild.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.wrong_guild.desc"),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        role = ctx.guild.get_role(config["role_id"])
        
        if not role:
            embed = discord.Embed(
                title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.role_deleted.title"),
                description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.error_types.role_deleted.desc", autorole_id=autorole_id),
                color=discord.Color.orange()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.info.title"),
            description=await TH.get_for_user(self.bot, ctx.author.id, "cog_autorole.messages.info.desc", autorole_id=autorole_id),
            color=discord.Color.blue()
        )
        embed.add_field(name="Rolle", value=role.mention, inline=True)
        embed.add_field(name="Status", value="🟢 Aktiviert" if config["enabled"] else "🔴 Deaktiviert", inline=True)
        embed.add_field(name="Mitglieder mit dieser Rolle", value=str(len(role.members)), inline=True)
        embed.add_field(name="Rollen-ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Autorole-ID", value=f"`{autorole_id}`", inline=True)
        
        await ctx.respond(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Event: Wird ausgelöst, wenn ein neues Mitglied dem Server beitritt"""
        
        role_ids = await self.db.get_enabled_autoroles(member.guild.id)
        
        if not role_ids:
            return
        
        roles_to_add = []
        
        for role_id in role_ids:
            role = member.guild.get_role(role_id)
            if role and role.position < member.guild.me.top_role.position:
                roles_to_add.append(role)
        
        if not roles_to_add:
            return
        
        try:
            audit_reason = TH.get("de", "cog_autorole.system.audit_reason")
            await member.add_roles(*roles_to_add, reason=audit_reason)
            
            role_names = ", ".join([r.name for r in roles_to_add])
            log_msg = TH.get("de", "cog_autorole.system.console_log", role_names=role_names, member_name=member.name)
            print(log_msg)
        except discord.Forbidden:
            print(TH.get("de", "cog_autorole.system.error_forbidden"))
        except discord.HTTPException as e:
            print(TH.get("de", "cog_autorole.system.error_http", error=str(e)))

def setup(bot):
    bot.add_cog(AutoRole(bot))