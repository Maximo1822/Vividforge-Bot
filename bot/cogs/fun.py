import discord
from discord.ext import commands
from discord import app_commands
import random

EIGHT_BALL_RESPONSES = [
    "It is certain. ✅","It is decidedly so. ✅","Without a doubt. ✅","Yes, definitely. ✅",
    "You may rely on it. ✅","As I see it, yes. ✅","Most likely. ✅","Outlook good. ✅",
    "Yes. ✅","Signs point to yes. ✅","Reply hazy, try again. 🔄","Ask again later. 🔄",
    "Better not tell you now. 🔄","Cannot predict now. 🔄","Concentrate and ask again. 🔄",
    "Don't count on it. ❌","My reply is no. ❌","My sources say no. ❌",
    "Outlook not so good. ❌","Very doubtful. ❌",
]


class Fun(commands.Cog):
    """Fun commands — prefix and slash."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ══════════════════════════════════════════════════════════════════════════
    # COINFLIP
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="coinflip", aliases=["flip","coin"])
    async def coinflip_prefix(self, ctx):
        """Flip a coin. Usage: !coinflip"""
        await self._send_coinflip(ctx)

    @app_commands.command(name="coinflip", description="Flip a coin — Heads or Tails!")
    async def coinflip_slash(self, interaction: discord.Interaction):
        await self._send_coinflip(interaction, slash=True)

    async def _send_coinflip(self, ctx_or_inter, slash=False):
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        embed = discord.Embed(title="🪙 Coin Flip", description=f"The coin landed on **{result}**!", color=discord.Color.gold())
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # ROLL
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="roll", aliases=["dice"])
    async def roll_prefix(self, ctx, dice: str = "1d6"):
        """Roll dice. Usage: !roll [NdN]"""
        await self._send_roll(ctx, dice)

    @app_commands.command(name="roll", description="Roll dice in NdN format (e.g. 2d6, 1d20).")
    @app_commands.describe(dice="Dice notation, e.g. 2d6 or 1d20 (default: 1d6)")
    async def roll_slash(self, interaction: discord.Interaction, dice: str = "1d6"):
        await self._send_roll(interaction, dice, slash=True)

    async def _send_roll(self, ctx_or_inter, dice: str, slash=False):
        try:
            parts = dice.lower().split("d")
            if len(parts) != 2:
                raise ValueError
            num, sides = int(parts[0]), int(parts[1])
            if not (1 <= num <= 20 and 2 <= sides <= 100):
                raise ValueError
        except (ValueError, IndexError):
            embed = discord.Embed(description="❌ Use `NdN` format, e.g. `2d6` or `1d20` (1–20 dice, 2–100 sides).", color=discord.Color.red())
            if slash:
                return await ctx_or_inter.response.send_message(embed=embed, ephemeral=True)
            return await ctx_or_inter.send(embed=embed)

        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls)
        roll_str = "  +  ".join(f"`{r}`" for r in rolls)
        embed = discord.Embed(title="🎲 Dice Roll", color=discord.Color.blurple())
        embed.add_field(name="Rolls", value=roll_str, inline=False)
        if num > 1:
            embed.add_field(name="Total", value=f"**{total}**", inline=False)
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # CHOOSE
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="choose", aliases=["pick"])
    async def choose_prefix(self, ctx, *options: str):
        """Choose between options. Usage: !choose "a" "b" "c" """
        if len(options) < 2:
            return await ctx.send(embed=discord.Embed(description='❌ Provide at least 2 options. Quote multi-word options.', color=discord.Color.red()))
        await self._send_choose(ctx, list(options))

    @app_commands.command(name="choose", description="Let the bot pick between up to 5 options.")
    @app_commands.describe(option1="First option", option2="Second option", option3="Third option (optional)", option4="Fourth option (optional)", option5="Fifth option (optional)")
    async def choose_slash(self, interaction: discord.Interaction, option1: str, option2: str, option3: str = "", option4: str = "", option5: str = ""):
        options = [o for o in [option1, option2, option3, option4, option5] if o]
        await self._send_choose(interaction, options, slash=True)

    async def _send_choose(self, ctx_or_inter, options: list[str], slash=False):
        choice = random.choice(options)
        embed = discord.Embed(title="🤔 I Choose...", description=f"**{choice}**", color=discord.Color.blurple())
        embed.set_footer(text=f"From {len(options)} options")
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════════════
    # 8-BALL
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="8ball", aliases=["eightball"])
    async def eight_ball_prefix(self, ctx, *, question: str):
        """Ask the 8-ball. Usage: !8ball Will I win?"""
        await self._send_8ball(ctx, question)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a yes/no question.")
    @app_commands.describe(question="Your yes/no question")
    async def eight_ball_slash(self, interaction: discord.Interaction, question: str):
        await self._send_8ball(interaction, question, slash=True)

    async def _send_8ball(self, ctx_or_inter, question: str, slash=False):
        response = random.choice(EIGHT_BALL_RESPONSES)
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.dark_purple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        author = ctx_or_inter.user if slash else ctx_or_inter.author
        embed.set_footer(text=f"Asked by {author}", icon_url=author.display_avatar.url)
        if slash:
            await ctx_or_inter.response.send_message(embed=embed)
        else:
            await ctx_or_inter.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
