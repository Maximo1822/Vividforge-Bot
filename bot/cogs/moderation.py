import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import re


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_duration(duration_str: str) -> timedelta | None:
    match = re.fullmatch(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return timedelta(**{{"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}[unit]: value})


def mod_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


async def _send_interaction_error(interaction: discord.Interaction, msg: str):
    embed = discord.Embed(description=f"❌ {msg}", color=discord.Color.red())
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Duration choices for /timeout ────────────────────────────────────────────

DURATION_UNITS = [
    app_commands.Choice(name="Seconds", value="s"),
    app_commands.Choice(name="Minutes", value="m"),
    app_commands.Choice(name="Hours",   value="h"),
    app_commands.Choice(name="Days",    value="d"),
]


class Moderation(commands.Cog):
    """Moderation commands — prefix (!kick) and slash (/kick)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings: dict[int, dict[int, list[str]]] = {}

    # ══════════════════════════════════════════════════════════════════════════
    # KICK
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided."):
        """Kick a member. Usage: !kick @member [reason]"""
        await self._do_kick(ctx, member, reason)

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        await self._do_kick(interaction, member, reason, slash=True)

    async def _do_kick(self, ctx_or_inter, member: discord.Member, reason: str, slash=False):
        author = ctx_or_inter.user if slash else ctx_or_inter.author
        guild  = ctx_or_inter.guild

        if member == author:
            return await self._reply(ctx_or_inter, mod_embed("❌ Error", "You cannot kick yourself.", discord.Color.red()), slash, ephemeral=True)
        if member.top_role >= author.top_role:
            return await self._reply(ctx_or_inter, mod_embed("❌ Error", "You cannot kick someone with an equal or higher role.", discord.Color.red()), slash, ephemeral=True)

        try:
            await member.send(embed=mod_embed("👢 You were kicked", f"You were kicked from **{guild.name}**.\n**Reason:** {reason}", discord.Color.orange()))
        except discord.Forbidden:
            pass
        await member.kick(reason=f"{author} — {reason}")
        await self._reply(ctx_or_inter, mod_embed("👢 Member Kicked", f"**{member}** has been kicked.\n**Reason:** {reason}", discord.Color.orange()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # BAN
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided."):
        """Ban a member. Usage: !ban @member [reason]"""
        await self._do_ban(ctx, member, reason)

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban", delete_days="Days of messages to delete (0–7)")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided.", delete_days: app_commands.Range[int, 0, 7] = 0):
        await self._do_ban(interaction, member, reason, delete_days=delete_days, slash=True)

    async def _do_ban(self, ctx_or_inter, member: discord.Member, reason: str, delete_days: int = 0, slash=False):
        author = ctx_or_inter.user if slash else ctx_or_inter.author
        guild  = ctx_or_inter.guild

        if member == author:
            return await self._reply(ctx_or_inter, mod_embed("❌ Error", "You cannot ban yourself.", discord.Color.red()), slash, ephemeral=True)
        if member.top_role >= author.top_role:
            return await self._reply(ctx_or_inter, mod_embed("❌ Error", "You cannot ban someone with an equal or higher role.", discord.Color.red()), slash, ephemeral=True)

        try:
            await member.send(embed=mod_embed("🔨 You were banned", f"You were banned from **{guild.name}**.\n**Reason:** {reason}", discord.Color.dark_red()))
        except discord.Forbidden:
            pass
        await member.ban(reason=f"{author} — {reason}", delete_message_days=delete_days)
        await self._reply(ctx_or_inter, mod_embed("🔨 Member Banned", f"**{member}** has been banned.\n**Reason:** {reason}", discord.Color.dark_red()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # UNBAN
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_prefix(self, ctx, *, user_id: int):
        """Unban a user by ID. Usage: !unban <user_id>"""
        await self._do_unban(ctx, user_id)

    @app_commands.command(name="unban", description="Unban a user by their Discord ID.")
    @app_commands.describe(user_id="The Discord user ID to unban")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def unban_slash(self, interaction: discord.Interaction, user_id: str):
        try:
            await self._do_unban(interaction, int(user_id), slash=True)
        except ValueError:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "That doesn't look like a valid user ID.", discord.Color.red()), ephemeral=True)

    async def _do_unban(self, ctx_or_inter, user_id: int, slash=False):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx_or_inter.guild.unban(user)
            await self._reply(ctx_or_inter, mod_embed("✅ Unbanned", f"**{user}** has been unbanned.", discord.Color.green()), slash)
        except discord.NotFound:
            await self._reply(ctx_or_inter, mod_embed("❌ Error", "That user is not banned or doesn't exist.", discord.Color.red()), slash, ephemeral=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TIMEOUT
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="timeout", aliases=["mute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout_prefix(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided."):
        """Timeout a member. Usage: !timeout @member 10m [reason]"""
        delta = parse_duration(duration)
        if not delta:
            return await ctx.send(embed=mod_embed("❌ Invalid Duration", "Use `10s`, `5m`, `2h`, `1d`.", discord.Color.red()))
        await self._do_timeout(ctx, member, delta, reason)

    @app_commands.command(name="timeout", description="Timeout (mute) a member for a set duration.")
    @app_commands.describe(member="Member to timeout", amount="Duration number", unit="Duration unit", reason="Reason for the timeout")
    @app_commands.choices(unit=DURATION_UNITS)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def timeout_slash(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 10000], unit: app_commands.Choice[str], reason: str = "No reason provided."):
        delta = timedelta(**{{"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}[unit.value]: amount})
        if delta > timedelta(days=28):
            return await interaction.response.send_message(embed=mod_embed("❌ Error", "Timeout cannot exceed 28 days.", discord.Color.red()), ephemeral=True)
        await self._do_timeout(interaction, member, delta, reason, slash=True, duration_label=f"{amount} {unit.name.lower()}")

    async def _do_timeout(self, ctx_or_inter, member: discord.Member, delta: timedelta, reason: str, slash=False, duration_label: str = ""):
        author = ctx_or_inter.user if slash else ctx_or_inter.author
        if member.top_role >= author.top_role:
            return await self._reply(ctx_or_inter, mod_embed("❌ Error", "You cannot timeout someone with an equal or higher role.", discord.Color.red()), slash, ephemeral=True)
        await member.timeout(delta, reason=f"{author} — {reason}")
        label = duration_label or str(delta)
        await self._reply(ctx_or_inter, mod_embed("🔇 Timed Out", f"**{member}** timed out for **{label}**.\n**Reason:** {reason}", discord.Color.yellow()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # UNTIMEOUT
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="untimeout", aliases=["unmute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided."):
        """Remove a timeout. Usage: !untimeout @member"""
        await self._do_untimeout(ctx, member, reason)

    @app_commands.command(name="untimeout", description="Remove a timeout from a member.")
    @app_commands.describe(member="Member to remove timeout from", reason="Reason")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def untimeout_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        await self._do_untimeout(interaction, member, reason, slash=True)

    async def _do_untimeout(self, ctx_or_inter, member: discord.Member, reason: str, slash=False):
        await member.timeout(None, reason=reason)
        await self._reply(ctx_or_inter, mod_embed("🔊 Timeout Removed", f"**{member}**'s timeout has been removed.", discord.Color.green()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # WARN
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided."):
        """Warn a member. Usage: !warn @member [reason]"""
        await self._do_warn(ctx, member, reason)

    @app_commands.command(name="warn", description="Warn a member and log it.")
    @app_commands.describe(member="Member to warn", reason="Reason for the warning")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        await self._do_warn(interaction, member, reason, slash=True)

    async def _do_warn(self, ctx_or_inter, member: discord.Member, reason: str, slash=False):
        guild = ctx_or_inter.guild
        user_warns = self.warnings.setdefault(guild.id, {}).setdefault(member.id, [])
        user_warns.append(reason)
        try:
            await member.send(embed=mod_embed("⚠️ Warning", f"You were warned in **{guild.name}**.\n**Reason:** {reason}\n**Total:** {len(user_warns)}", discord.Color.yellow()))
        except discord.Forbidden:
            pass
        await self._reply(ctx_or_inter, mod_embed("⚠️ Member Warned", f"**{member}** warned.\n**Reason:** {reason}\n**Total warnings:** {len(user_warns)}", discord.Color.yellow()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # WARNINGS
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="warnings", aliases=["warns"])
    @commands.has_permissions(manage_messages=True)
    async def warnings_prefix(self, ctx, member: discord.Member):
        """View warnings. Usage: !warnings @member"""
        await self._do_warnings(ctx, member)

    @app_commands.command(name="warnings", description="View the warnings for a member.")
    @app_commands.describe(member="Member to check")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        await self._do_warnings(interaction, member, slash=True)

    async def _do_warnings(self, ctx_or_inter, member: discord.Member, slash=False):
        user_warns = self.warnings.get(ctx_or_inter.guild.id, {}).get(member.id, [])
        if not user_warns:
            return await self._reply(ctx_or_inter, mod_embed("📋 Warnings", f"**{member}** has no warnings.", discord.Color.green()), slash)
        entries = "\n".join(f"`{i+1}.` {r}" for i, r in enumerate(user_warns))
        embed = discord.Embed(title=f"⚠️ Warnings for {member}", description=entries, color=discord.Color.yellow())
        embed.set_footer(text=f"Total: {len(user_warns)}")
        await self._reply(ctx_or_inter, embed, slash)

    # ══════════════════════════════════════════════════════════════════════════
    # CLEAR WARNINGS
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="clearwarnings", aliases=["clearwarns"])
    @commands.has_permissions(administrator=True)
    async def clearwarnings_prefix(self, ctx, member: discord.Member):
        """Clear warnings. Usage: !clearwarnings @member"""
        await self._do_clearwarnings(ctx, member)

    @app_commands.command(name="clearwarnings", description="Clear all warnings for a member.")
    @app_commands.describe(member="Member to clear warnings for")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        await self._do_clearwarnings(interaction, member, slash=True)

    async def _do_clearwarnings(self, ctx_or_inter, member: discord.Member, slash=False):
        self.warnings.get(ctx_or_inter.guild.id, {}).pop(member.id, None)
        await self._reply(ctx_or_inter, mod_embed("✅ Cleared", f"All warnings for **{member}** cleared.", discord.Color.green()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # PURGE
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_prefix(self, ctx, amount: int):
        """Delete messages. Usage: !purge 20"""
        await self._do_purge(ctx, amount)

    @app_commands.command(name="purge", description="Delete a number of messages from this channel.")
    @app_commands.describe(amount="Number of messages to delete (1–100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def purge_slash(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        await self._do_purge(interaction, amount, slash=True)

    async def _do_purge(self, ctx_or_inter, amount: int, slash=False):
        if slash:
            await ctx_or_inter.response.defer(ephemeral=True)
            deleted = await ctx_or_inter.channel.purge(limit=amount)
            await ctx_or_inter.followup.send(embed=mod_embed("🗑️ Purged", f"Deleted **{len(deleted)}** message(s).", discord.Color.blurple()), ephemeral=True)
        else:
            if not 1 <= amount <= 100:
                return await ctx_or_inter.send(embed=mod_embed("❌ Error", "Amount must be 1–100.", discord.Color.red()))
            deleted = await ctx_or_inter.channel.purge(limit=amount + 1)
            msg = await ctx_or_inter.send(embed=mod_embed("🗑️ Purged", f"Deleted **{len(deleted)-1}** message(s).", discord.Color.blurple()))
            await msg.delete(delay=5)

    # ══════════════════════════════════════════════════════════════════════════
    # SLOWMODE
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode_prefix(self, ctx, seconds: int):
        """Set slowmode. Usage: !slowmode 5"""
        await self._do_slowmode(ctx, seconds)

    @app_commands.command(name="slowmode", description="Set the slowmode delay for this channel (0 to disable).")
    @app_commands.describe(seconds="Delay in seconds (0 to disable, max 21600)")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def slowmode_slash(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 0, 21600]):
        await self._do_slowmode(interaction, seconds, slash=True)

    async def _do_slowmode(self, ctx_or_inter, seconds: int, slash=False):
        await ctx_or_inter.channel.edit(slowmode_delay=seconds)
        msg = "Slowmode **disabled**." if seconds == 0 else f"Slowmode set to **{seconds}s**."
        await self._reply(ctx_or_inter, mod_embed("⏱️ Slowmode", msg, discord.Color.blurple()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # LOCK / UNLOCK
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock_prefix(self, ctx):
        """Lock channel. Usage: !lock"""
        await self._do_lock(ctx, True)

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock_prefix(self, ctx):
        """Unlock channel. Usage: !unlock"""
        await self._do_lock(ctx, False)

    @app_commands.command(name="lock", description="Lock the current channel so members cannot send messages.")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def lock_slash(self, interaction: discord.Interaction):
        await self._do_lock(interaction, True, slash=True)

    @app_commands.command(name="unlock", description="Unlock the current channel.")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def unlock_slash(self, interaction: discord.Interaction):
        await self._do_lock(interaction, False, slash=True)

    async def _do_lock(self, ctx_or_inter, lock: bool, slash=False):
        channel = ctx_or_inter.channel
        overwrite = channel.overwrites_for(ctx_or_inter.guild.default_role)
        overwrite.send_messages = False if lock else None
        await channel.set_permissions(ctx_or_inter.guild.default_role, overwrite=overwrite)
        if lock:
            await self._reply(ctx_or_inter, mod_embed("🔒 Locked", f"{channel.mention} has been locked.", discord.Color.red()), slash)
        else:
            await self._reply(ctx_or_inter, mod_embed("🔓 Unlocked", f"{channel.mention} has been unlocked.", discord.Color.green()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # NICK
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="nick")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick_prefix(self, ctx, member: discord.Member, *, nickname: str | None = None):
        """Change nickname. Usage: !nick @member [name]"""
        await self._do_nick(ctx, member, nickname)

    @app_commands.command(name="nick", description="Change or reset a member's nickname.")
    @app_commands.describe(member="The member", nickname="New nickname (leave blank to reset)")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    @app_commands.checks.bot_has_permissions(manage_nicknames=True)
    async def nick_slash(self, interaction: discord.Interaction, member: discord.Member, nickname: str = ""):
        await self._do_nick(interaction, member, nickname or None, slash=True)

    async def _do_nick(self, ctx_or_inter, member: discord.Member, nickname: str | None, slash=False):
        old = member.display_name
        await member.edit(nick=nickname)
        if nickname:
            await self._reply(ctx_or_inter, mod_embed("✏️ Nickname Changed", f"**{old}** → **{nickname}**", discord.Color.blurple()), slash)
        else:
            await self._reply(ctx_or_inter, mod_embed("✏️ Nickname Reset", f"**{member}**'s nickname reset.", discord.Color.blurple()), slash)

    # ══════════════════════════════════════════════════════════════════════════
    # Shared reply helper
    # ══════════════════════════════════════════════════════════════════════════

    async def _reply(self, ctx_or_inter, embed: discord.Embed, slash: bool, ephemeral: bool = False):
        if slash:
            if ctx_or_inter.response.is_done():
                await ctx_or_inter.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                await ctx_or_inter.response.send_message(embed=embed, ephemeral=ephemeral)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # Error handlers for slash commands
    # ══════════════════════════════════════════════════════════════════════════

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        msg = "An error occurred."
        if isinstance(error, app_commands.MissingPermissions):
            msg = "You don't have permission to use this command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = f"I'm missing permissions: `{', '.join(error.missing_permissions)}`"
        embed = discord.Embed(description=f"❌ {msg}", color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
