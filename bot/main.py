import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot intents
# message_content is a privileged intent — must be enabled in the Discord
# Developer Portal under Bot → Privileged Gateway Intents.
intents = discord.Intents.default()
intents.message_content = True   # required for prefix commands
intents.guilds = True

# Bot setup
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,  # We use a custom help command
    description="A moderation & utility Discord bot.",
)

# Load cogs
COGS = [
    "cogs.moderation",
    "cogs.general",
    "cogs.fun",
    "cogs.embeds",
]


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"   Serving {len(bot.guilds)} guild(s).")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="VividForge | !help",
        )
    )


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Global error handler."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            embed=discord.Embed(
                description="❌ You don't have permission to use this command.",
                color=discord.Color.red(),
            )
        )
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(
            embed=discord.Embed(
                description=f"❌ I'm missing permissions: `{', '.join(error.missing_permissions)}`",
                color=discord.Color.red(),
            )
        )
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(
            embed=discord.Embed(
                description="❌ Member not found.",
                color=discord.Color.red(),
            )
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            embed=discord.Embed(
                description=f"❌ Missing argument: `{error.param.name}`.\nUse `!help {ctx.command}` for usage.",
                color=discord.Color.red(),
            )
        )
    elif isinstance(error, commands.CommandNotFound):
        pass  # Silently ignore unknown commands
    else:
        await ctx.send(
            embed=discord.Embed(
                description=f"❌ An error occurred: `{error}`",
                color=discord.Color.red(),
            )
        )
        print(f"Unhandled error in {ctx.command}: {error}")


async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"   Loaded cog: {cog}")
            except Exception as e:
                print(f"   ⚠ Failed to load cog {cog}: {e}")
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
