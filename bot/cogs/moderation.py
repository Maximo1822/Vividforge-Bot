import discord
from discord.ext import commands
from datetime import timedelta
import re


def parse_duration(duration_str: str) -> timedelta | None:
    """Parse a duration string like '10m', '2h', '1d' into a timedelta."""
    match = re.fullmatch(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    return timedelta(**{units[unit]: value})


def mod_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    return embed


class Moderation(commands.Cog):
    """Moderation commands for keeping the server safe."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # In-memory warn store: {guild_id: {user_id: [reason, ...]}}
        self.warnings: dict[int, dict[int, list[str]]] = {}

    # ── Kick ─────────────────────────────────────────────────────────────────

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ):
        """Kick a member from the server.

        Usage: !kick @member [reason]
        """
        if member == ctx.author:
            return await ctx.send(
                embed=mod_embed("❌ Error", "You cannot kick yourself.", discord.Color.red())
            )
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(
                embed=mod_embed("❌ Error", "You cannot kick someone with an equal or higher role.", discord.Color.red())
            )

        try:
            await member.send(
                embed=mod_embed(
                    "👢 You were kicked",
                    f"You were kicked from **{ctx.guild.name}**.\n**Reason:** {reason}",
                    discord.Color.orange(),
                )
            )
        except discord.Forbidden:
            pass

        await member.kick(reason=f"{ctx.author} — {reason}")
        await ctx.send(
            embed=mod_embed(
                "👢 Member Kicked",
                f"**{member}** has been kicked.\n**Reason:** {reason}",
                discord.Color.orange(),
            )
        )

    # ── Ban ──────────────────────────────────────────────────────────────────

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ):
        """Ban a member from the server.

        Usage: !ban @member [reason]
        """
        if member == ctx.author:
            return await ctx.send(
                embed=mod_embed("❌ Error", "You cannot ban yourself.", discord.Color.red())
            )
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(
                embed=mod_embed("❌ Error", "You cannot ban someone with an equal or higher role.", discord.Color.red())
            )

        try:
            await member.send(
                embed=mod_embed(
                    "🔨 You were banned",
                    f"You were banned from **{ctx.guild.name}**.\n**Reason:** {reason}",
                    discord.Color.dark_red(),
                )
            )
        except discord.Forbidden:
            pass

        await member.ban(reason=f"{ctx.author} — {reason}", delete_message_days=0)
        await ctx.send(
            embed=mod_embed(
                "🔨 Member Banned",
                f"**{member}** has been banned.\n**Reason:** {reason}",
                discord.Color.dark_red(),
            )
        )

    # ── Unban ────────────────────────────────────────────────────────────────

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, user_id: int):
        """Unban a user by their ID.

        Usage: !unban <user_id>
        """
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
            await ctx.send(
                embed=mod_embed(
                    "✅ Member Unbanned",
                    f"**{user}** has been unbanned.",
                    discord.Color.green(),
                )
            )
        except discord.NotFound:
            await ctx.send(
                embed=mod_embed("❌ Error", "That user is not banned or doesn't exist.", discord.Color.red())
            )

    # ── Timeout (mute) ───────────────────────────────────────────────────────

    @commands.command(name="timeout", aliases=["mute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "No reason provided.",
    ):
        """Timeout (mute) a member for a specified duration.

        Duration format: 10s, 5m, 2h, 1d (max 28d)
        Usage: !timeout @member 10m [reason]
        """
        delta = parse_duration(duration)
        if delta is None:
            return await ctx.send(
                embed=mod_embed(
                    "❌ Invalid Duration",
                    "Use format like `10s`, `5m`, `2h`, `1d`.",
                    discord.Color.red(),
                )
            )

        if delta > timedelta(days=28):
            return await ctx.send(
                embed=mod_embed("❌ Error", "Timeout duration cannot exceed 28 days.", discord.Color.red())
            )

        if member.top_role >= ctx.author.top_role:
            return await ctx.send(
                embed=mod_embed("❌ Error", "You cannot timeout someone with an equal or higher role.", discord.Color.red())
            )

        await member.timeout(delta, reason=f"{ctx.author} — {reason}")
        await ctx.send(
            embed=mod_embed(
                "🔇 Member Timed Out",
                f"**{member}** has been timed out for **{duration}**.\n**Reason:** {reason}",
                discord.Color.yellow(),
            )
        )

    # ── Untimeout ────────────────────────────────────────────────────────────

    @commands.command(name="untimeout", aliases=["unmute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ):
        """Remove a timeout from a member.

        Usage: !untimeout @member [reason]
        """
        await member.timeout(None, reason=f"{ctx.author} — {reason}")
        await ctx.send(
            embed=mod_embed(
                "🔊 Timeout Removed",
                f"**{member}**'s timeout has been removed.",
                discord.Color.green(),
            )
        )

    # ── Warn ─────────────────────────────────────────────────────────────────

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ):
        """Warn a member and log it.

        Usage: !warn @member [reason]
        """
        guild_warns = self.warnings.setdefault(ctx.guild.id, {})
        user_warns = guild_warns.setdefault(member.id, [])
        user_warns.append(reason)
        count = len(user_warns)

        try:
            await member.send(
                embed=mod_embed(
                    "⚠️ You were warned",
                    f"You received a warning in **{ctx.guild.name}**.\n**Reason:** {reason}\n**Total warnings:** {count}",
                    discord.Color.yellow(),
                )
            )
        except discord.Forbidden:
            pass

        await ctx.send(
            embed=mod_embed(
                "⚠️ Member Warned",
                f"**{member}** has been warned.\n**Reason:** {reason}\n**Total warnings:** {count}",
                discord.Color.yellow(),
            )
        )

    # ── Warnings ─────────────────────────────────────────────────────────────

    @commands.command(name="warnings", aliases=["warns"])
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        """View the warnings for a member.

        Usage: !warnings @member
        """
        guild_warns = self.warnings.get(ctx.guild.id, {})
        user_warns = guild_warns.get(member.id, [])

        if not user_warns:
            return await ctx.send(
                embed=mod_embed(
                    "📋 Warnings",
                    f"**{member}** has no warnings.",
                    discord.Color.green(),
                )
            )

        entries = "\n".join(f"`{i + 1}.` {r}" for i, r in enumerate(user_warns))
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member}",
            description=entries,
            color=discord.Color.yellow(),
        )
        embed.set_footer(text=f"Total: {len(user_warns)} warning(s)")
        await ctx.send(embed=embed)

    # ── Clear Warnings ───────────────────────────────────────────────────────

    @commands.command(name="clearwarnings", aliases=["clearwarns"])
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member.

        Usage: !clearwarnings @member
        """
        guild_warns = self.warnings.get(ctx.guild.id, {})
        guild_warns.pop(member.id, None)
        await ctx.send(
            embed=mod_embed(
                "✅ Warnings Cleared",
                f"All warnings for **{member}** have been cleared.",
                discord.Color.green(),
            )
        )

    # ── Purge ────────────────────────────────────────────────────────────────

    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Delete a number of messages from the channel (1–100).

        Usage: !purge 20
        """
        if not 1 <= amount <= 100:
            return await ctx.send(
                embed=mod_embed("❌ Error", "Amount must be between 1 and 100.", discord.Color.red())
            )

        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command itself
        msg = await ctx.send(
            embed=mod_embed(
                "🗑️ Messages Purged",
                f"Deleted **{len(deleted) - 1}** message(s).",
                discord.Color.blurple(),
            )
        )
        await msg.delete(delay=5)

    # ── Slowmode ─────────────────────────────────────────────────────────────

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """Set the slowmode delay for this channel (0 to disable).

        Usage: !slowmode 5
        """
        if not 0 <= seconds <= 21600:
            return await ctx.send(
                embed=mod_embed("❌ Error", "Slowmode must be between 0 and 21600 seconds.", discord.Color.red())
            )

        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            msg = "Slowmode has been **disabled**."
        else:
            msg = f"Slowmode set to **{seconds} second(s)**."

        await ctx.send(embed=mod_embed("⏱️ Slowmode Updated", msg, discord.Color.blurple()))

    # ── Lock / Unlock ────────────────────────────────────────────────────────

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        """Lock the current channel so members cannot send messages.

        Usage: !lock
        """
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(
            embed=mod_embed("🔒 Channel Locked", f"{ctx.channel.mention} has been locked.", discord.Color.red())
        )

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        """Unlock the current channel.

        Usage: !unlock
        """
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(
            embed=mod_embed("🔓 Channel Unlocked", f"{ctx.channel.mention} has been unlocked.", discord.Color.green())
        )

    # ── Nick ─────────────────────────────────────────────────────────────────

    @commands.command(name="nick")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        nickname: str | None = None,
    ):
        """Change or reset a member's nickname.

        Usage: !nick @member NewName
               !nick @member  (resets to username)
        """
        old_nick = member.display_name
        await member.edit(nick=nickname)
        if nickname:
            await ctx.send(
                embed=mod_embed(
                    "✏️ Nickname Changed",
                    f"**{old_nick}** → **{nickname}**",
                    discord.Color.blurple(),
                )
            )
        else:
            await ctx.send(
                embed=mod_embed(
                    "✏️ Nickname Reset",
                    f"**{member}**'s nickname has been reset.",
                    discord.Color.blurple(),
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
