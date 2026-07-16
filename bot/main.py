import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

COGS = [
    "cogs.moderation",
    "cogs.general",
    "cogs.fun",
    "cogs.embeds",
]


class VividForgeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            description="VividForge — moderation, utility & fun.",
        )

    async def setup_hook(self):
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"   Loaded cog: {cog}")
            except Exception as e:
                print(f"   ⚠ Failed to load cog {cog}: {e}")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        print(f"   Serving {len(self.guilds)} guild(s).")

        # Sync slash commands to every guild the bot is in — instant propagation.
        # Global sync (no guild arg) can take up to 1 hour; per-guild is immediate.
        synced_guilds = []
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                synced_guilds.append(guild.name)
            except Exception as e:
                print(f"   ⚠ Failed to sync to {guild.name}: {e}")

        if synced_guilds:
            print(f"   ✅ Slash commands synced to: {', '.join(synced_guilds)}")
        else:
            print("   ⚠ No guilds to sync to.")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="VividForge | !help",
            )
        )

    async def on_guild_join(self, guild: discord.Guild):
        """Sync slash commands immediately when the bot joins a new server."""
        try:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"   ✅ Synced slash commands to new guild: {guild.name}")
        except Exception as e:
            print(f"   ⚠ Failed to sync to {guild.name}: {e}")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(description="❌ You don't have permission to use this command.", color=discord.Color.red()))
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(description=f"❌ I'm missing permissions: `{', '.join(error.missing_permissions)}`", color=discord.Color.red()))
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(embed=discord.Embed(description="❌ Member not found.", color=discord.Color.red()))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(description=f"❌ Missing argument: `{error.param.name}`.\nUse `!help {ctx.command}` for usage.", color=discord.Color.red()))
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await ctx.send(embed=discord.Embed(description=f"❌ An error occurred: `{error}`", color=discord.Color.red()))
            print(f"Unhandled error in {ctx.command}: {error}")


bot = VividForgeBot()


@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx: commands.Context):
    """Force-sync slash commands to this server. Owner only."""
    try:
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(embed=discord.Embed(
            title="✅ Synced",
            description=f"Synced **{len(synced)}** slash command(s) to **{ctx.guild.name}**.",
            color=discord.Color.green(),
        ))
    except Exception as e:
        await ctx.send(embed=discord.Embed(description=f"❌ Sync failed: `{e}`", color=discord.Color.red()))


if __name__ == "__main__":
    import asyncio
    asyncio.run(bot.start(TOKEN))
