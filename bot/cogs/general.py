import discord
from discord.ext import commands
from discord import app_commands
import time

START_TIME = time.time()


def seconds_to_hms(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


class General(commands.Cog):
    """General utility commands — prefix and slash."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ══════════════════════════════════════════════════════════════════════════
    # HELP (prefix only — slash has built-in Discord UI)
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="help")
    async def help(self, ctx, *, command_name: str | None = None):
        """Show commands. Usage: !help [command]"""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if cmd is None:
                return await ctx.send(embed=discord.Embed(description=f"❌ Command `{command_name}` not found.", color=discord.Color.red()))
            embed = discord.Embed(title=f"📖 !{cmd.name}", description=cmd.help or "No description.", color=discord.Color.blurple())
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`!{a}`" for a in cmd.aliases))
            return await ctx.send(embed=embed)

        embed = discord.Embed(title="📖 VividForge Commands", description="Prefix: `!`  |  Slash: `/`  |  `!help <command>` for details.", color=discord.Color.blurple())
        categories = {
            "🛡️ Moderation": ["kick","ban","unban","timeout","untimeout","warn","warnings","clearwarnings","purge","slowmode","lock","unlock","nick"],
            "🔧 General":    ["ping","uptime","serverinfo","userinfo","avatar","roleinfo"],
            "🎲 Fun":        ["coinflip","roll","choose","8ball"],
            "🖼️ Embeds":    ["embed","embedjson","embedcolors"],
        }
        for cat, cmds in categories.items():
            valid = [f"`!{c}`" for c in cmds if self.bot.get_command(c)]
            if valid:
                embed.add_field(name=cat, value="  ".join(valid), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # PING
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="ping")
    async def ping_prefix(self, ctx):
        """Check latency. Usage: !ping"""
        await self._send_ping(ctx)

    @app_commands.command(name="ping", description="Check the bot's response latency.")
    async def ping_slash(self, interaction: discord.Interaction):
        await self._send_ping(interaction, slash=True)

    async def _send_ping(self, ctx_or_inter, slash=False):
        ms = round(self.bot.latency * 1000)
        color = discord.Color.green() if ms < 100 else discord.Color.yellow() if ms < 200 else discord.Color.red()
        embed = discord.Embed(title="🏓 Pong!", description=f"Gateway latency: **{ms} ms**", color=color)
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # UPTIME
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="uptime")
    async def uptime_prefix(self, ctx):
        """Show uptime. Usage: !uptime"""
        await self._send_uptime(ctx)

    @app_commands.command(name="uptime", description="Show how long the bot has been running.")
    async def uptime_slash(self, interaction: discord.Interaction):
        await self._send_uptime(interaction, slash=True)

    async def _send_uptime(self, ctx_or_inter, slash=False):
        embed = discord.Embed(title="⏱️ Uptime", description=f"Running for **{seconds_to_hms(time.time() - START_TIME)}**.", color=discord.Color.blurple())
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # SERVER INFO
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="serverinfo", aliases=["server","guildinfo"])
    async def serverinfo_prefix(self, ctx):
        """Server info. Usage: !serverinfo"""
        await self._send_serverinfo(ctx)

    @app_commands.command(name="serverinfo", description="Display information about this server.")
    async def serverinfo_slash(self, interaction: discord.Interaction):
        await self._send_serverinfo(interaction, slash=True)

    async def _send_serverinfo(self, ctx_or_inter, slash=False):
        guild = ctx_or_inter.guild
        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots
        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 ID", value=str(guild.id), inline=True)
        embed.add_field(name="📅 Created", value=discord.utils.format_dt(guild.created_at, style="D"), inline=True)
        embed.add_field(name="👥 Members", value=f"{humans} humans, {bots} bots", inline=True)
        embed.add_field(name="💬 Channels", value=f"{len(guild.text_channels)} text · {len(guild.voice_channels)} voice", inline=True)
        embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="✨ Boosts", value=f"{guild.premium_subscription_count} (Tier {guild.premium_tier})", inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)
        if guild.description:
            embed.add_field(name="📝 Description", value=guild.description, inline=False)
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # USER INFO
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="userinfo", aliases=["whois","user"])
    async def userinfo_prefix(self, ctx, member: discord.Member | None = None):
        """User info. Usage: !userinfo [@member]"""
        await self._send_userinfo(ctx, member or ctx.author)

    @app_commands.command(name="userinfo", description="Display information about a member.")
    @app_commands.describe(member="Member to inspect (defaults to yourself)")
    async def userinfo_slash(self, interaction: discord.Interaction, member: discord.Member | None = None):
        await self._send_userinfo(interaction, member or interaction.user, slash=True)

    async def _send_userinfo(self, ctx_or_inter, member: discord.Member, slash=False):
        roles = [r.mention for r in reversed(member.roles) if r != ctx_or_inter.guild.default_role]
        embed = discord.Embed(title=str(member), color=member.color if member.color != discord.Color.default() else discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=str(member.id), inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="📅 Created", value=discord.utils.format_dt(member.created_at, style="D"), inline=True)
        embed.add_field(name="📥 Joined", value=discord.utils.format_dt(member.joined_at, style="D") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="🎨 Top Role", value=member.top_role.mention, inline=True)
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles[:10]) + (" …" if len(roles) > 10 else ""), inline=False)
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # AVATAR
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="avatar", aliases=["av","pfp"])
    async def avatar_prefix(self, ctx, member: discord.Member | None = None):
        """Show avatar. Usage: !avatar [@member]"""
        await self._send_avatar(ctx, member or ctx.author)

    @app_commands.command(name="avatar", description="Show a member's avatar.")
    @app_commands.describe(member="Member (defaults to yourself)")
    async def avatar_slash(self, interaction: discord.Interaction, member: discord.Member | None = None):
        await self._send_avatar(interaction, member or interaction.user, slash=True)

    async def _send_avatar(self, ctx_or_inter, member: discord.Member, slash=False):
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.blurple())
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Links", value=f"[PNG]({member.display_avatar.with_format('png').url}) | [JPG]({member.display_avatar.with_format('jpg').url}) | [WEBP]({member.display_avatar.with_format('webp').url})")
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # ROLE INFO
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="roleinfo", aliases=["role"])
    async def roleinfo_prefix(self, ctx, *, role: discord.Role):
        """Role info. Usage: !roleinfo @role"""
        await self._send_roleinfo(ctx, role)

    @app_commands.command(name="roleinfo", description="Display information about a role.")
    @app_commands.describe(role="The role to inspect")
    async def roleinfo_slash(self, interaction: discord.Interaction, role: discord.Role):
        await self._send_roleinfo(interaction, role, slash=True)

    async def _send_roleinfo(self, ctx_or_inter, role: discord.Role, slash=False):
        embed = discord.Embed(title=f"🎭 {role.name}", color=role.color if role.color != discord.Color.default() else discord.Color.blurple())
        embed.add_field(name="🆔 ID", value=str(role.id), inline=True)
        embed.add_field(name="🎨 Color", value=str(role.color), inline=True)
        embed.add_field(name="📅 Created", value=discord.utils.format_dt(role.created_at, style="D"), inline=True)
        embed.add_field(name="📌 Position", value=str(role.position), inline=True)
        embed.add_field(name="🔒 Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="👁️ Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="👥 Members", value=str(len(role.members)), inline=True)
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
