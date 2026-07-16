import discord
from discord.ext import commands
import random


EIGHT_BALL_RESPONSES = [
    # Positive
    "It is certain. ✅",
    "It is decidedly so. ✅",
    "Without a doubt. ✅",
    "Yes, definitely. ✅",
    "You may rely on it. ✅",
    "As I see it, yes. ✅",
    "Most likely. ✅",
    "Outlook good. ✅",
    "Yes. ✅",
    "Signs point to yes. ✅",
    # Neutral
    "Reply hazy, try again. 🔄",
    "Ask again later. 🔄",
    "Better not tell you now. 🔄",
    "Cannot predict now. 🔄",
    "Concentrate and ask again. 🔄",
    # Negative
    "Don't count on it. ❌",
    "My reply is no. ❌",
    "My sources say no. ❌",
    "Outlook not so good. ❌",
    "Very doubtful. ❌",
]


class Fun(commands.Cog):
    """Fun and miscellaneous commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Coin Flip ─────────────────────────────────────────────────────────────

    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coinflip(self, ctx: commands.Context):
        """Flip a coin — Heads or Tails!

        Usage: !coinflip
        """
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    # ── Dice Roll ────────────────────────────────────────────────────────────

    @commands.command(name="roll", aliases=["dice"])
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        """Roll dice in NdN format (e.g. 2d6, 1d20).

        Usage: !roll [NdN]  (default: 1d6)
        """
        try:
            parts = dice.lower().split("d")
            if len(parts) != 2:
                raise ValueError
            num, sides = int(parts[0]), int(parts[1])
            if not (1 <= num <= 20 and 2 <= sides <= 100):
                raise ValueError
        except (ValueError, IndexError):
            return await ctx.send(
                embed=discord.Embed(
                    description="❌ Invalid format. Use `NdN` e.g. `2d6` or `1d20` (1–20 dice, 2–100 sides).",
                    color=discord.Color.red(),
                )
            )

        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls)
        roll_str = "  +  ".join(f"`{r}`" for r in rolls)

        embed = discord.Embed(title="🎲 Dice Roll", color=discord.Color.blurple())
        embed.add_field(name="Rolls", value=roll_str, inline=False)
        if num > 1:
            embed.add_field(name="Total", value=f"**{total}**", inline=False)
        await ctx.send(embed=embed)

    # ── Choose ───────────────────────────────────────────────────────────────

    @commands.command(name="choose", aliases=["pick"])
    async def choose(self, ctx: commands.Context, *options: str):
        """Let the bot choose between options (separate with spaces, quote multi-word options).

        Usage: !choose "go for a walk" "watch TV" "read a book"
        """
        if len(options) < 2:
            return await ctx.send(
                embed=discord.Embed(
                    description='❌ Provide at least 2 options. Quote multi-word options: `!choose "option one" "option two"`',
                    color=discord.Color.red(),
                )
            )
        choice = random.choice(options)
        embed = discord.Embed(
            title="🤔 I Choose...",
            description=f"**{choice}**",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"From {len(options)} options")
        await ctx.send(embed=embed)

    # ── 8-Ball ───────────────────────────────────────────────────────────────

    @commands.command(name="8ball", aliases=["eightball"])
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        """Ask the magic 8-ball a yes/no question.

        Usage: !8ball Will I win today?
        """
        response = random.choice(EIGHT_BALL_RESPONSES)
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.dark_purple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_footer(text=f"Asked by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
