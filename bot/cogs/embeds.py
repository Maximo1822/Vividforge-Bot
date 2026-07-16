import discord
from discord.ext import commands
from discord import app_commands
import datetime
import shlex

# ── Color registry ────────────────────────────────────────────────────────────

NAMED_COLORS: dict[str, int] = {
    "red": 0xE74C3C, "green": 0x2ECC71, "blue": 0x3498DB, "yellow": 0xF1C40F,
    "orange": 0xE67E22, "purple": 0x9B59B6, "pink": 0xFF69B4, "cyan": 0x1ABC9C,
    "white": 0xFFFFFF, "black": 0x000000, "gold": 0xFFD700, "blurple": 0x5865F2,
    "dark": 0x2C2F33, "navy": 0x34495E, "teal": 0x008080, "lime": 0x00FF00,
    "maroon": 0x800000, "violet": 0xEE82EE, "indigo": 0x4B0082, "coral": 0xFF7F50,
}

COLOR_CHOICES = [
    app_commands.Choice(name=name.capitalize(), value=name)
    for name in list(NAMED_COLORS.keys())[:25]  # Discord limit: 25 choices
]


def resolve_color(raw: str) -> discord.Color:
    raw = raw.strip().lower()
    if raw in NAMED_COLORS:
        return discord.Color(NAMED_COLORS[raw])
    try:
        return discord.Color(int(raw.lstrip("#"), 16))
    except ValueError:
        return discord.Color.blurple()


# ── UI: Add Field modal ───────────────────────────────────────────────────────

class AddFieldModal(discord.ui.Modal, title="Add a Field"):
    field_name = discord.ui.TextInput(
        label="Field Name",
        placeholder="e.g. Status, Notes, Links …",
        max_length=256,
        required=True,
    )
    field_value = discord.ui.TextInput(
        label="Field Value",
        style=discord.TextStyle.long,
        placeholder="The content of this field …",
        max_length=1024,
        required=True,
    )
    inline = discord.ui.TextInput(
        label="Inline? (yes / no)",
        placeholder="yes",
        default="no",
        max_length=3,
        required=False,
    )

    def __init__(self, view: "EmbedActionsView"):
        super().__init__()
        self.embed_view = view

    async def on_submit(self, interaction: discord.Interaction):
        inline = self.inline.value.strip().lower() in ("yes", "y", "true", "1")
        self.embed_view.embed.add_field(
            name=self.field_name.value,
            value=self.field_value.value,
            inline=inline,
        )
        await interaction.response.edit_message(
            content="**Preview** (updated with new field)",
            embed=self.embed_view.embed,
            view=self.embed_view,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"❌ Something went wrong: `{error}`", ephemeral=True)


# ── UI: Advanced options modal ────────────────────────────────────────────────

class AdvancedOptionsModal(discord.ui.Modal, title="Advanced Embed Options"):
    title_url = discord.ui.TextInput(
        label="Title URL (makes title clickable)",
        placeholder="https://example.com",
        required=False,
        max_length=500,
    )
    thumbnail_url = discord.ui.TextInput(
        label="Thumbnail URL (small image, top-right)",
        placeholder="https://example.com/thumb.png",
        required=False,
        max_length=500,
    )
    author_name = discord.ui.TextInput(
        label="Author Name",
        placeholder="e.g. VividForge Bot",
        required=False,
        max_length=256,
    )
    author_icon = discord.ui.TextInput(
        label="Author Icon URL",
        placeholder="https://example.com/icon.png",
        required=False,
        max_length=500,
    )
    timestamp = discord.ui.TextInput(
        label="Show Timestamp? (yes / no)",
        placeholder="no",
        default="no",
        max_length=3,
        required=False,
    )

    def __init__(self, view: "EmbedActionsView"):
        super().__init__()
        self.embed_view = view

    async def on_submit(self, interaction: discord.Interaction):
        emb = self.embed_view.embed
        if self.title_url.value:
            emb.url = self.title_url.value
        if self.thumbnail_url.value:
            emb.set_thumbnail(url=self.thumbnail_url.value)
        if self.author_name.value:
            emb.set_author(
                name=self.author_name.value,
                icon_url=self.author_icon.value if self.author_icon.value else None,
            )
        if self.timestamp.value.strip().lower() in ("yes", "y", "true", "1"):
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await interaction.response.edit_message(
            content="**Preview** (advanced options applied)",
            embed=emb,
            view=self.embed_view,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"❌ Something went wrong: `{error}`", ephemeral=True)


# ── UI: Edit main embed modal ─────────────────────────────────────────────────

class EditEmbedModal(discord.ui.Modal, title="Edit Embed"):
    new_title = discord.ui.TextInput(label="Title", required=False, max_length=256)
    new_description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, required=False, max_length=4096)
    new_color = discord.ui.TextInput(label="Color (name or #hex)", required=False, max_length=30, placeholder="e.g. gold or #FFD700")
    new_footer = discord.ui.TextInput(label="Footer", required=False, max_length=2048)
    new_image = discord.ui.TextInput(label="Image URL", required=False, max_length=500)

    def __init__(self, view: "EmbedActionsView"):
        super().__init__()
        self.embed_view = view
        emb = view.embed
        if emb.title:
            self.new_title.default = emb.title
        if emb.description:
            self.new_description.default = emb.description
        # Use getattr to safely read proxy objects that may not exist
        footer_text = getattr(emb.footer, "text", None)
        if footer_text:
            self.new_footer.default = footer_text
        image_url = getattr(emb.image, "url", None)
        if image_url:
            self.new_image.default = image_url

    async def on_submit(self, interaction: discord.Interaction):
        emb = self.embed_view.embed
        if self.new_title.value:       emb.title = self.new_title.value
        if self.new_description.value: emb.description = self.new_description.value
        if self.new_color.value:       emb.color = resolve_color(self.new_color.value)
        if self.new_footer.value:      emb.set_footer(text=self.new_footer.value)
        if self.new_image.value:       emb.set_image(url=self.new_image.value)
        await interaction.response.edit_message(
            content="**Preview** (edited)",
            embed=emb,
            view=self.embed_view,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"❌ Something went wrong: `{error}`", ephemeral=True)


# ── UI: Action buttons shown after preview ────────────────────────────────────

class EmbedActionsView(discord.ui.View):
    def __init__(self, embed: discord.Embed, author_id: int):
        super().__init__(timeout=300)
        self.embed = embed
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Only the embed creator can use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Send Here", style=discord.ButtonStyle.success)
    async def send_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(embed=self.embed)
        await interaction.response.edit_message(content="✅ Embed sent!", embed=None, view=None)

    @discord.ui.button(label="📤 Send to Channel", style=discord.ButtonStyle.primary)
    async def send_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SendToChannelModal(self))

    @discord.ui.button(label="➕ Add Field", style=discord.ButtonStyle.secondary)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddFieldModal(self))

    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.secondary)
    async def edit_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditEmbedModal(self))

    @discord.ui.button(label="⚙️ Advanced", style=discord.ButtonStyle.secondary)
    async def advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdvancedOptionsModal(self))

    @discord.ui.button(label="🗑️ Clear Fields", style=discord.ButtonStyle.danger, row=1)
    async def clear_fields(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.clear_fields()
        await interaction.response.edit_message(content="**Preview** (fields cleared)", embed=self.embed, view=self)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelled.", embed=None, view=None)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        print(f"EmbedActionsView error on {item}: {error}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Button error: `{error}`", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Button error: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── UI: Send to channel modal ─────────────────────────────────────────────────

class SendToChannelModal(discord.ui.Modal, title="Send to Channel"):
    channel_id = discord.ui.TextInput(
        label="Channel ID or #mention",
        placeholder="Paste a channel ID or right-click → Copy ID",
        required=True,
        max_length=30,
    )

    def __init__(self, view: EmbedActionsView):
        super().__init__()
        self.embed_view = view

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.channel_id.value.strip().strip("<#>")
        try:
            ch = interaction.guild.get_channel(int(raw))
            if ch is None:
                raise ValueError
        except (ValueError, AttributeError):
            return await interaction.response.send_message("❌ Channel not found. Make sure you paste a valid channel ID.", ephemeral=True)

        await ch.send(embed=self.embed_view.embed)
        await interaction.response.edit_message(content=f"✅ Embed sent to {ch.mention}!", embed=None, view=None)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"❌ Something went wrong: `{error}`", ephemeral=True)


# ── Main embed builder modal (triggered by /embed) ───────────────────────────

class EmbedBuilderModal(discord.ui.Modal, title="🖼️ Embed Builder"):
    embed_title = discord.ui.TextInput(
        label="Title",
        placeholder="Your embed title …",
        required=False,
        max_length=256,
    )
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="Main body text. Markdown supported: **bold**, *italic*, `code` …",
        required=False,
        max_length=4096,
    )
    color = discord.ui.TextInput(
        label="Side-bar Color  (name or #hex)",
        placeholder="e.g.  gold  /  #FFD700  /  blurple",
        default="blurple",
        required=False,
        max_length=30,
    )
    footer = discord.ui.TextInput(
        label="Footer Text",
        placeholder="e.g. VividForge • Today",
        required=False,
        max_length=2048,
    )
    image_url = discord.ui.TextInput(
        label="Image URL  (large bottom image)",
        placeholder="https://example.com/image.png",
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Defer immediately — this acknowledges the interaction within 3 s
        # and gives us 15 minutes to send the real response via followup.
        await interaction.response.defer(ephemeral=True)
        try:
            embed = discord.Embed(color=resolve_color(self.color.value or "blurple"))
            if self.embed_title.value:  embed.title       = self.embed_title.value
            if self.description.value:  embed.description = self.description.value
            if self.footer.value:       embed.set_footer(text=self.footer.value)
            if self.image_url.value:    embed.set_image(url=self.image_url.value)

            has_content = any([self.embed_title.value, self.description.value, self.image_url.value])
            if not has_content:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        description="❌ Add at least a **title**, **description**, or **image URL**.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

            view = EmbedActionsView(embed=embed, author_id=interaction.user.id)
            await interaction.followup.send(
                content="**Preview** — use the buttons below to refine and send.",
                embed=embed,
                view=view,
                ephemeral=True,
            )
        except Exception as e:
            print(f"EmbedBuilderModal.on_submit error: {e}")
            try:
                await interaction.followup.send(f"❌ Error building embed: `{e}`", ephemeral=True)
            except Exception:
                pass

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"EmbedBuilderModal error: {error}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Something went wrong: `{error}`", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Something went wrong: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── Cog ───────────────────────────────────────────────────────────────────────

class Embeds(commands.Cog):
    """Embed builder — guided /embed and flexible !embed."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /embed (slash — opens guided modal) ───────────────────────────────────

    @app_commands.command(name="embed", description="Open the guided embed builder.")
    async def embed_slash(self, interaction: discord.Interaction):
        """Opens a step-by-step form to build and send a custom embed."""
        try:
            await interaction.response.send_modal(EmbedBuilderModal())
        except Exception as e:
            print(f"embed_slash error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Could not open the embed builder: `{e}`", ephemeral=True)

    # ── !embed (prefix — flag-based, power user) ──────────────────────────────

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_prefix(self, ctx: commands.Context, *, raw: str = ""):
        """Send a custom embed using flags.

        Flags (all optional):
          --title         Title text
          --description   Body (markdown supported)
          --color         Name or hex  (e.g. red, #ff0000)
          --footer        Footer text
          --author        Author name
          --image         Large bottom image URL
          --thumbnail     Small top-right image URL
          --field         "Name | Value"  (repeat for multiple fields)
          --inline        yes/no for the preceding --field
          --channel       #channel to send to
          --timestamp     yes to show current timestamp

        Available colors: red green blue yellow orange purple pink cyan
                          white black gold blurple dark navy teal lime
                          maroon violet indigo coral  (or any #hex)

        Examples:
          !embed --title Hello --description Welcome! --color gold
          !embed --title Stats --field Wins | 42 --inline yes --field Losses | 3
          !embed --title Announce --image https://... --channel #general
        """
        if not raw:
            return await ctx.send(embed=self._help_embed())

        try:
            tokens = tuple(shlex.split(raw))
        except ValueError:
            tokens = tuple(raw.split())

        flags = self._parse_flags(tokens)
        if not flags:
            return await ctx.send(embed=self._help_embed())

        color = resolve_color(flags.get("color", "blurple"))
        embed = discord.Embed(color=color)

        if "title"       in flags: embed.title       = flags["title"][:256]
        if "description" in flags: embed.description = flags["description"][:4096]
        if "footer"      in flags: embed.set_footer(text=flags["footer"][:2048])
        if "author"      in flags: embed.set_author(name=flags["author"][:256])
        if "image"       in flags: embed.set_image(url=flags["image"])
        if "thumbnail"   in flags: embed.set_thumbnail(url=flags["thumbnail"])
        if flags.get("timestamp", "").lower() in ("yes", "true", "1"):
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

        for name, value, inline in self._collect_fields(tokens):
            embed.add_field(name=name[:256], value=value[:1024], inline=inline)

        has_content = any([
            flags.get("title"), flags.get("description"), flags.get("image"),
            flags.get("thumbnail"), embed.fields,
        ])
        if not has_content:
            return await ctx.send(embed=discord.Embed(description="❌ The embed has no content.", color=discord.Color.red()))

        channel = ctx.channel
        if "channel" in flags:
            try:
                ch = ctx.guild.get_channel(int(flags["channel"].strip("<#>")))
                if ch:
                    channel = ch
            except (ValueError, AttributeError):
                pass

        await channel.send(embed=embed)
        if channel != ctx.channel:
            await ctx.send(embed=discord.Embed(description=f"✅ Embed sent to {channel.mention}.", color=discord.Color.green()), delete_after=5)
        await ctx.message.delete()

    # ── !embedjson ────────────────────────────────────────────────────────────

    @commands.command(name="embedjson")
    @commands.has_permissions(manage_messages=True)
    async def embedjson(self, ctx: commands.Context, *, raw_json: str = ""):
        """Send an embed from raw JSON (power users).

        Usage: !embedjson {"title": "Hi", "color": 5814783}
        """
        import json, re
        raw_json = re.sub(r"^```(?:json)?\n?", "", raw_json.strip())
        raw_json = re.sub(r"\n?```$", "", raw_json)
        if not raw_json:
            return await ctx.send(embed=discord.Embed(description="❌ Provide a JSON object.", color=discord.Color.red()))
        try:
            data = json.loads(raw_json)
            embed = discord.Embed.from_dict(data)
        except Exception as e:
            return await ctx.send(embed=discord.Embed(description=f"❌ Error: `{e}`", color=discord.Color.red()))
        await ctx.send(embed=embed)
        await ctx.message.delete()

    # ── !embedcolors ──────────────────────────────────────────────────────────

    @commands.command(name="embedcolors", aliases=["colors"])
    async def embedcolors(self, ctx: commands.Context):
        """Show all named colors. Usage: !embedcolors"""
        embed = discord.Embed(title="🎨 Available Colors", description="Use with `--color` (prefix) or the color field in `/embed`.\nYou can also use any hex code: `#FF5733`", color=discord.Color.blurple())
        chunk = "\n".join(f"`{name:<10}` `#{hex(val)[2:].upper().zfill(6)}`" for name, val in NAMED_COLORS.items())
        embed.add_field(name="Named Colors", value=chunk, inline=False)
        await ctx.send(embed=embed)

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_flags(tokens: tuple[str, ...]) -> dict[str, str]:
        flags: dict[str, str] = {}
        current_key = None
        current_val: list[str] = []
        for token in tokens:
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

    @staticmethod
    def _collect_fields(tokens: tuple[str, ...]) -> list[tuple[str, str, bool]]:
        fields: list[tuple[str, str, bool]] = []
        i = 0
        while i < len(tokens):
            if tokens[i] == "--field":
                i += 1
                val_tokens: list[str] = []
                while i < len(tokens) and not tokens[i].startswith("--"):
                    val_tokens.append(tokens[i])
                    i += 1
                raw = " ".join(val_tokens)
                name, _, value = raw.partition("|") if "|" in raw else ("Field", "", raw)
                inline = False
                if i < len(tokens) and tokens[i] == "--inline":
                    i += 1
                    if i < len(tokens) and not tokens[i].startswith("--"):
                        inline = tokens[i].lower() in ("yes", "true", "1")
                        i += 1
                    else:
                        inline = True
                fields.append((name.strip(), value.strip(), inline))
            else:
                i += 1
        return fields

    @staticmethod
    def _help_embed() -> discord.Embed:
        return discord.Embed(
            title="🖼️ Embed Command Help",
            description=(
                "**Slash command (recommended — guided):**\n`/embed` — opens a pop-up form\n\n"
                "**Prefix command (power user):**\n"
                "```\n!embed --title Hello --description World --color gold\n```\n"
                "**Available flags:** `--title` `--description` `--color` `--footer` `--author` "
                "`--image` `--thumbnail` `--field` `--inline` `--channel` `--timestamp`\n\n"
                "Use `!embedcolors` to see all named colors."
            ),
            color=discord.Color.blurple(),
        )


    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        print(f"Embeds app command error: {error}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Something went wrong: `{error}`", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Something went wrong: `{error}`", ephemeral=True)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))
