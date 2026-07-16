import discord
from discord.ext import commands


# ── Helpers ───────────────────────────────────────────────────────────────────

NAMED_COLORS: dict[str, int] = {
    "red": 0xE74C3C,
    "green": 0x2ECC71,
    "blue": 0x3498DB,
    "yellow": 0xF1C40F,
    "orange": 0xE67E22,
    "purple": 0x9B59B6,
    "pink": 0xFF69B4,
    "cyan": 0x1ABC9C,
    "white": 0xFFFFFF,
    "black": 0x000000,
    "gold": 0xFFD700,
    "blurple": 0x5865F2,
    "dark": 0x2C2F33,
    "navy": 0x34495E,
}


def resolve_color(raw: str) -> discord.Color:
    """Accept a named color or a hex string (#RRGGBB / RRGGBB)."""
    raw = raw.strip().lower()
    if raw in NAMED_COLORS:
        return discord.Color(NAMED_COLORS[raw])
    raw = raw.lstrip("#")
    try:
        return discord.Color(int(raw, 16))
    except ValueError:
        return discord.Color.blurple()


def parse_flags(args: tuple[str, ...]) -> dict:
    """
    Parse a flat tuple of tokens into a flag dict.
    Flags start with '--', everything after the flag name up to the
    next flag is that flag's value.

    Example input tokens:
        --title Hello World --description Some text --color red
    """
    flags: dict[str, str] = {}
    current_key = None
    current_val: list[str] = []

    for token in args:
        if token.startswith("--"):
            if current_key is not None:
                flags[current_key] = " ".join(current_val).strip()
            current_key = token[2:].lower()
            current_val = []
        else:
            current_val.append(token)

    if current_key is not None:
        flags[current_key] = " ".join(current_val).strip()

    return flags


# ── Cog ───────────────────────────────────────────────────────────────────────

class Embeds(commands.Cog):
    """Create and send fully customisable embeds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !embed ────────────────────────────────────────────────────────────────

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx: commands.Context, *, raw: str = ""):
        """Send a fully customisable embed with image support.

        Flags (all optional):
          --title         Title text
          --description   Body text (supports markdown)
          --color         Side-bar color: name or hex (e.g. red, #ff0000)
          --footer        Footer text
          --author        Author name shown at the top
          --image         URL of a large image shown at the bottom
          --thumbnail     URL of a small image in the top-right corner
          --field         Add a field: "Field Name | Field Value" (repeat for multiple)
          --inline        "yes" to make the last --field inline (default: no)
          --channel       #channel mention to send to (defaults to current channel)
          --timestamp     "yes" to show current time in the footer

        Available color names:
          red, green, blue, yellow, orange, purple, pink, cyan,
          white, black, gold, blurple, dark, navy

        Example:
          !embed --title Hello --description Welcome! --color gold --image https://...
        """
        if not raw:
            return await ctx.send(embed=self._help_embed())

        # Split into tokens preserving quoted strings
        import shlex
        try:
            tokens = tuple(shlex.split(raw))
        except ValueError:
            tokens = tuple(raw.split())

        flags = parse_flags(tokens)

        if not flags:
            return await ctx.send(embed=self._help_embed())

        # ── Build embed ───────────────────────────────────────────────────────
        color = resolve_color(flags.get("color", "blurple"))
        embed = discord.Embed(color=color)

        if "title" in flags:
            embed.title = flags["title"][:256]
        if "description" in flags:
            embed.description = flags["description"][:4096]
        if "footer" in flags:
            embed.set_footer(text=flags["footer"][:2048])
        if "author" in flags:
            embed.set_author(name=flags["author"][:256])
        if "image" in flags:
            embed.set_image(url=flags["image"])
        if "thumbnail" in flags:
            embed.set_thumbnail(url=flags["thumbnail"])
        if flags.get("timestamp", "").lower() in ("yes", "true", "1"):
            import datetime
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

        # Fields — collect all --field occurrences from raw positional pass
        # Because parse_flags only keeps the last duplicate key we re-parse:
        field_entries = self._collect_fields(tokens)
        for name, value, inline in field_entries:
            embed.add_field(name=name[:256], value=value[:1024], inline=inline)

        # Validate embed has at least some content
        if not any([embed.title, embed.description, embed.fields, embed.image, embed.thumbnail]):
            return await ctx.send(
                embed=discord.Embed(
                    description="❌ The embed has no content. Add at least `--title`, `--description`, or `--image`.",
                    color=discord.Color.red(),
                )
            )

        # Target channel
        channel = ctx.channel
        if "channel" in flags:
            channel_mention = flags["channel"].strip("<#>")
            try:
                fetched = ctx.guild.get_channel(int(channel_mention))
                if fetched:
                    channel = fetched
            except (ValueError, AttributeError):
                pass

        await channel.send(embed=embed)

        # Confirm if sent to a different channel
        if channel != ctx.channel:
            await ctx.send(
                embed=discord.Embed(
                    description=f"✅ Embed sent to {channel.mention}.",
                    color=discord.Color.green(),
                ),
                delete_after=5,
            )
        await ctx.message.delete()

    # ── !embedjson ────────────────────────────────────────────────────────────

    @commands.command(name="embedjson")
    @commands.has_permissions(manage_messages=True)
    async def embedjson(self, ctx: commands.Context, *, raw_json: str = ""):
        """Send an embed from a raw JSON object (for power users).

        The JSON must follow Discord's embed structure.
        Wrap the JSON in a code block or paste it directly.

        Example:
          !embedjson {"title": "Hi", "description": "Hello!", "color": 5814783}
        """
        import json, re

        # Strip markdown code blocks if present
        raw_json = re.sub(r"^```(?:json)?\n?", "", raw_json.strip())
        raw_json = re.sub(r"\n?```$", "", raw_json)

        if not raw_json:
            return await ctx.send(
                embed=discord.Embed(
                    description="❌ Provide a JSON object after the command.",
                    color=discord.Color.red(),
                )
            )

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"❌ Invalid JSON: `{e}`",
                    color=discord.Color.red(),
                )
            )

        try:
            embed = discord.Embed.from_dict(data)
        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"❌ Could not build embed: `{e}`",
                    color=discord.Color.red(),
                )
            )

        await ctx.send(embed=embed)
        await ctx.message.delete()

    # ── !embedcolors ──────────────────────────────────────────────────────────

    @commands.command(name="embedcolors", aliases=["colors"])
    async def embedcolors(self, ctx: commands.Context):
        """Show all available named colors for the --color flag.

        Usage: !embedcolors
        """
        embed = discord.Embed(
            title="🎨 Available Embed Colors",
            description="Use these names with `--color` or supply any hex code like `--color #ff5733`.",
            color=discord.Color.blurple(),
        )
        swatches = "\n".join(
            f"`{name}` — #{hex(value)[2:].upper().zfill(6)}"
            for name, value in NAMED_COLORS.items()
        )
        embed.add_field(name="Named Colors", value=swatches, inline=False)
        await ctx.send(embed=embed)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _collect_fields(self, tokens: tuple[str, ...]) -> list[tuple[str, str, bool]]:
        """
        Walk the token list and collect every --field occurrence,
        paired with the nearest following --inline flag.
        Returns list of (name, value, inline).
        """
        fields: list[tuple[str, str, bool]] = []
        i = 0
        while i < len(tokens):
            if tokens[i] == "--field":
                # Gather value tokens until the next '--' flag
                i += 1
                val_tokens: list[str] = []
                while i < len(tokens) and not tokens[i].startswith("--"):
                    val_tokens.append(tokens[i])
                    i += 1
                raw_field = " ".join(val_tokens)
                # Expect "Name | Value" separator
                if "|" in raw_field:
                    name, _, value = raw_field.partition("|")
                else:
                    name, value = "Field", raw_field

                # Peek ahead for --inline immediately after this field
                inline = False
                if i < len(tokens) and tokens[i] == "--inline":
                    i += 1
                    # Optional 'yes'/'no' value
                    if i < len(tokens) and not tokens[i].startswith("--"):
                        inline = tokens[i].lower() in ("yes", "true", "1")
                        i += 1
                    else:
                        inline = True

                fields.append((name.strip(), value.strip(), inline))
            else:
                i += 1
        return fields

    def _help_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📋 !embed — Usage",
            description=(
                "Build and send a custom embed using flags.\n\n"
                "**Basic example:**\n"
                "```\n!embed --title My Title --description Hello world --color blue\n```\n"
                "**With image & footer:**\n"
                "```\n!embed --title Announcement --description Read below --image https://example.com/img.png --footer VividForge Bot --color gold\n```\n"
                "**Send to another channel:**\n"
                "```\n!embed --title Hello --description Hi there --channel #general\n```\n"
                "**With fields:**\n"
                "```\n!embed --title Stats --field Wins | 42 --inline yes --field Losses | 3 --inline yes\n```\n"
                "**All flags:** `--title` `--description` `--color` `--footer` `--author` "
                "`--image` `--thumbnail` `--field` `--inline` `--channel` `--timestamp`\n\n"
                "Use `!embedcolors` to see all named colors.\n"
                "Use `!embedjson` to send an embed from raw JSON."
            ),
            color=discord.Color.blurple(),
        )
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))
