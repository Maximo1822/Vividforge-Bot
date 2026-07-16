import discord
from discord.ext import commands
import platform
import time


START_TIME = time.time()


def seconds_to_hms(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


class General(commands.Cog):
    """General utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Help ─────────────────────────────────────────────────────────────────

    @commands.command(name="help")
    async def help(self, ctx: commands.Context, *, command_name: str | None = None):
        """Show a list of commands, or details about a specific one.

        Usage: !help
               !help ban
        """
        if command_name:
            cmd = self.bot.get_command(command_name)
            if cmd is None:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"❌ Command `{command_name}` not found.",
                        color=discord.Color.red(),
                    )
                )
            embed = discord.Embed(
                title=f"📖 !{cmd.name}",
                description=cmd.help or "No description available.",
                color=discord.Color.blurple(),
            )
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`!{a}`" for a in cmd.aliases), inline=False)
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="📖 Bot Commands",
            description="Prefix: `!`  |  Use `!help <command>` for details.",
            color=discord.Color.blurple(),
        )

        categories = {
            "🛡️ Moderation": ["kick", "ban", "unban", "timeout", "untimeout", "warn", "warnings", "clearwarnings", "purge", "slowmode", "lock", "unlock", "nick"],
            "🔧 General": ["help", "ping", "uptime", "serverinfo", "userinfo", "avatar", "roleinfo"],
            "🎲 Fun": ["coinflip", "roll", "choose", "8ball"],
        }

        for category, cmds in categories.items():
            valid = [f"`!{c}`" for c in cmds if self.bot.get_command(c)]
            if valid:
                embed.add_field(name=category, value="  ".join(valid), inline=False)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    # ── Ping ─────────────────────────────────────────────────────────────────

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency.

        Usage: !ping
        """
        latency_ms = round(self.bot.latency * 1000)
        color = discord.Color.green() if latency_ms < 100 else discord.Color.yellow() if latency_ms < 200 else discord.Color.red()
        await ctx.send(
            embed=discord.Embed(
                title="🏓 Pong!",
                description=f"Gateway latency: **{latency_ms} ms**",
                color=color,
            )
        )

    # ── Uptime ───────────────────────────────────────────────────────────────

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        """Show how long the bot has been running.

        Usage: !uptime
        """
        elapsed = time.time() - START_TIME
        await ctx.send(
            embed=discord.Embed(
                title="⏱️ Uptime",
                description=f"Bot has been running for **{seconds_to_hms(elapsed)}**.",
                color=discord.Color.blurple(),
            )
        )

    # ── Server Info ──────────────────────────────────────────────────────────

    @commands.command(name="serverinfo", aliases=["server", "guildinfo"])
    async def serverinfo(self, ctx: commands.Context):
        """Display information about this server.

        Usage: !serverinfo
        """
        guild = ctx.guild
        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots

        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=str(guild.id), inline=True)
        embed.add_field(name="📅 Created", value=discord.utils.format_dt(guild.created_at, style="D"), inline=True)
        embed.add_field(name="👥 Members", value=f"{humans} humans, {bots} bots", inline=True)
        embed.add_field(name="💬 Channels", value=f"{len(guild.text_channels)} text, {len(guild.voice_channels)} voice", inline=True)
        embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="✨ Boosts", value=f"{guild.premium_subscription_count} (Tier {guild.premium_tier})", inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)

        if guild.description:
            embed.add_field(name="📝 Description", value=guild.description, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    # ── User Info ────────────────────────────────────────────────────────────

    @commands.command(name="userinfo", aliases=["whois", "user"])
    async def userinfo(self, ctx: commands.Context, member: discord.Member | None = None):
        """Display information about a member (defaults to yourself).

        Usage: !userinfo [@member]
        """
        member = member or ctx.author
        roles = [r.mention for r in reversed(member.roles) if r != ctx.guild.default_role]

        embed = discord.Embed(
            title=str(member),
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=str(member.id), inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="📅 Account Created", value=discord.utils.format_dt(member.created_at, style="D"), inline=True)
        embed.add_field(name="📥 Joined Server", value=discord.utils.format_dt(member.joined_at, style="D") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="🎨 Top Role", value=member.top_role.mention, inline=True)
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles[:10]) + (" …" if len(roles) > 10 else ""), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    # ── Avatar ───────────────────────────────────────────────────────────────

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member | None = None):
        """Show a member's avatar (defaults to yourself).

        Usage: !avatar [@member]
        """
        member = member or ctx.author
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Links", value=f"[PNG]({member.display_avatar.with_format('png').url}) | [JPG]({member.display_avatar.with_format('jpg').url}) | [WEBP]({member.display_avatar.with_format('webp').url})")
        await ctx.send(embed=embed)

    # ── Role Info ────────────────────────────────────────────────────────────

    @commands.command(name="roleinfo", aliases=["role"])
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        """Display information about a role.

        Usage: !roleinfo @role
        """
        embed = discord.Embed(
            title=f"🎭 {role.name}",
            color=role.color if role.color != discord.Color.default() else discord.Color.blurple(),
        )
        embed.add_field(name="🆔 ID", value=str(role.id), inline=True)
        embed.add_field(name="🎨 Color", value=str(role.color), inline=True)
        embed.add_field(name="📅 Created", value=discord.utils.format_dt(role.created_at, style="D"), inline=True)
        embed.add_field(name="📌 Position", value=str(role.position), inline=True)
        embed.add_field(name="🔒 Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="👁️ Displayed Separately", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="👥 Members", value=str(len(role.members)), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
