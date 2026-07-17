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


def resolve_color(raw: str) -> discord.Color:
    raw = raw.strip().lower()
    if raw in NAMED_COLORS:
        return discord.Color(NAMED_COLORS[raw])
    try:
        return discord.Color(int(raw.lstrip("#"), 16))
    except ValueError:
        return discord.Color.blurple()


# ── Modal: Step 1 — core fields ───────────────────────────────────────────────

class EmbedBuilderModal(discord.ui.Modal, title="Embed Builder — Step 1"):
    embed_title = discord.ui.TextInput(
        label="Title",
        placeholder="Your embed title…",
        required=False,
        max_length=256,
    )
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="Main body. Markdown works: **bold**, *italic*, `code`, > quote",
        required=False,
        max_length=4000,
    )
    color = discord.ui.TextInput(
        label="Color (name or #hex)",
        placeholder="e.g.  gold  /  #FFD700  /  blurple  /  red",
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
        label="Image URL (large bottom image)",
        placeholder="https://example.com/image.png",
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            embed = discord.Embed(color=resolve_color(self.color.value or "blurple"))
            if self.embed_title.value:
                embed.title = self.embed_title.value
            if self.description.value:
                embed.description = self.description.value
            if self.footer.value:
                embed.set_footer(text=self.footer.value)
            if self.image_url.value:
                embed.set_image(url=self.image_url.value)

            if not any([self.embed_title.value, self.description.value, self.image_url.value]):
                return await interaction.followup.send(
                    embed=discord.Embed(
                        description="❌ Add at least a **title**, **description**, or **image URL**.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

            view = EmbedActionsView(embed=embed, author_id=interaction.user.id)
            await interaction.followup.send(
                content=(
                    "**🖼️ Preview** — use the buttons to refine, then send.\n"
                    "-# ✏️ Edit core fields  •  ⚙️ Advanced (author, thumbnail, URL, timestamp)  "
                    "•  ➕ Add fields  •  📤 Pick a channel below"
                ),
                embed=embed,
                view=view,
                ephemeral=True,
            )
        except Exception as e:
            print(f"EmbedBuilderModal.on_submit error: {e}")
            try:
                await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)
            except Exception:
                pass

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"EmbedBuilderModal.on_error: {error}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Error: `{error}`", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Error: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── Modal: Edit core fields ───────────────────────────────────────────────────

class EditEmbedModal(discord.ui.Modal, title="Edit Embed"):
    new_title = discord.ui.TextInput(
        label="Title", required=False, max_length=256,
    )
    new_description = discord.ui.TextInput(
        label="Description", style=discord.TextStyle.long, required=False, max_length=4000,
    )
    new_color = discord.ui.TextInput(
        label="Color (name or #hex)", required=False, max_length=30,
        placeholder="e.g. gold or #FFD700",
    )
    new_footer = discord.ui.TextInput(
        label="Footer", required=False, max_length=2048,
    )
    new_image = discord.ui.TextInput(
        label="Image URL (large bottom image)", required=False, max_length=500,
    )

    def __init__(self, view: "EmbedActionsView"):
        super().__init__()
        self.embed_view = view
        emb = view.embed
        if emb.title:
            self.new_title.default = emb.title
        if emb.description:
            self.new_description.default = emb.description
        footer_text = getattr(emb.footer, "text", None)
        if footer_text:
            self.new_footer.default = footer_text
        image_url = getattr(emb.image, "url", None)
        if image_url:
            self.new_image.default = image_url

    async def on_submit(self, interaction: discord.Interaction):
        emb = self.embed_view.embed
        if self.new_title.value:
            emb.title = self.new_title.value
        if self.new_description.value:
            emb.description = self.new_description.value
        if self.new_color.value:
            emb.color = resolve_color(self.new_color.value)
        if self.new_footer.value:
            emb.set_footer(text=self.new_footer.value)
        if self.new_image.value:
            emb.set_image(url=self.new_image.value)
        await interaction.response.edit_message(
            content=(
                "**🖼️ Preview** (edited) — use the buttons to refine, then send.\n"
                "-# ✏️ Edit core fields  •  ⚙️ Advanced (author, thumbnail, URL, timestamp)  "
                "•  ➕ Add fields  •  📤 Pick a channel below"
            ),
            embed=emb,
            view=self.embed_view,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"EditEmbedModal.on_error: {error}")
        try:
            await interaction.response.send_message(f"❌ Error: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── Modal: Advanced options (author, thumbnail, title URL, timestamp) ─────────

class AdvancedOptionsModal(discord.ui.Modal, title="Advanced Options"):
    title_url = discord.ui.TextInput(
        label="Title URL (makes title a hyperlink)",
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
        placeholder="e.g. VividForge",
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
        emb = view.embed
        if emb.url:
            self.title_url.default = emb.url
        thumb_url = getattr(emb.thumbnail, "url", None)
        if thumb_url:
            self.thumbnail_url.default = thumb_url
        author_name = getattr(emb.author, "name", None)
        if author_name:
            self.author_name.default = author_name
        author_icon = getattr(emb.author, "icon_url", None)
        if author_icon:
            self.author_icon.default = author_icon

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
        else:
            emb.timestamp = None
        await interaction.response.edit_message(
            content=(
                "**🖼️ Preview** (advanced applied) — use the buttons to refine, then send.\n"
                "-# ✏️ Edit core fields  •  ⚙️ Advanced (author, thumbnail, URL, timestamp)  "
                "•  ➕ Add fields  •  📤 Pick a channel below"
            ),
            embed=emb,
            view=self.embed_view,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"AdvancedOptionsModal.on_error: {error}")
        try:
            await interaction.response.send_message(f"❌ Error: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── Modal: Add field ──────────────────────────────────────────────────────────

class AddFieldModal(discord.ui.Modal, title="Add a Field"):
    field_name = discord.ui.TextInput(
        label="Field Name",
        placeholder="e.g. Status, Members, Links…",
        max_length=256,
        required=True,
    )
    field_value = discord.ui.TextInput(
        label="Field Value",
        style=discord.TextStyle.long,
        placeholder="Content of this field (markdown supported)",
        max_length=1024,
        required=True,
    )
    inline = discord.ui.TextInput(
        label="Inline? (yes / no)  — side-by-side with other inline fields",
        placeholder="no",
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
            content=(
                "**🖼️ Preview** (field added) — use the buttons to refine, then send.\n"
                "-# ✏️ Edit core fields  •  ⚙️ Advanced (author, thumbnail, URL, timestamp)  "
                "•  ➕ Add fields  •  📤 Pick a channel below"
            ),
            embed=self.embed_view.embed,
            view=self.embed_view,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"AddFieldModal.on_error: {error}")
        try:
            await interaction.response.send_message(f"❌ Error: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── View: action buttons + channel select ─────────────────────────────────────

PREVIEW_HINT = (
    "**🖼️ Preview** — use the buttons to refine, then send.\n"
    "-# ✏️ Edit core fields  •  ⚙️ Advanced (author, thumbnail, URL, timestamp)  "
    "•  ➕ Add fields  •  📤 Pick a channel below"
)


class EmbedActionsView(discord.ui.View):
    def __init__(self, embed: discord.Embed, author_id: int):
        super().__init__(timeout=600)
        self.embed = embed
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the embed creator can use these controls.", ephemeral=True
            )
            return False
        return True

    # Row 0 ────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="✅ Send Here", style=discord.ButtonStyle.success, row=0)
    async def send_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(embed=self.embed)
        await interaction.response.edit_message(
            content=f"✅ Embed sent to {interaction.channel.mention}!", embed=None, view=None
        )

    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.primary, row=0)
    async def edit_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditEmbedModal(self))

    @discord.ui.button(label="⚙️ Advanced", style=discord.ButtonStyle.secondary, row=0)
    async def advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdvancedOptionsModal(self))

    @discord.ui.button(label="➕ Add Field", style=discord.ButtonStyle.secondary, row=0)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddFieldModal(self))

    @discord.ui.button(label="🗑️ Clear Fields", style=discord.ButtonStyle.danger, row=0)
    async def clear_fields(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.clear_fields()
        await interaction.response.edit_message(
            content=PREVIEW_HINT + "\n-# Fields cleared.",
            embed=self.embed,
            view=self,
        )

    # Row 1 ────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelled.", embed=None, view=None)

    # Row 2 — channel select (Discord native channel picker) ──────────────────

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="📤 Send to a channel…",
        row=2,
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1,
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        channel = select.values[0]
        try:
            await channel.send(embed=self.embed)
            await interaction.response.edit_message(
                content=f"✅ Embed sent to {channel.mention}!", embed=None, view=None
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ I don't have permission to send messages in {channel.mention}.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: `{e}`", ephemeral=True)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item
    ):
        print(f"EmbedActionsView error on {item}: {error}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Error: `{error}`", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Error: `{error}`", ephemeral=True)
        except Exception:
            pass


# ── Cog ───────────────────────────────────────────────────────────────────────

class Embeds(commands.Cog):
    """Embed builder — guided /embed and power-user !embed."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /embed ───────────────────────────────────────────────────────────────────

    @app_commands.command(name="embed", description="Open the guided embed builder.")
    async def embed_slash(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(EmbedBuilderModal())
        except Exception as e:
            print(f"embed_slash error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Could not open the embed builder: `{e}`", ephemeral=True
                )

    # !embed ───────────────────────────────────────────────────────────────────

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_prefix(self, ctx: commands.Context, *, raw: str = ""):
        """Build an embed with flags.

        Flags:
          --title        Title text
          --description  Body (markdown)
          --color        Name or #hex
          --footer       Footer text
          --author       Author name
          --image        Large bottom image URL
          --thumbnail    Small top-right image URL
          --field        "Name | Value"  (repeat for multiple)
          --inline       yes/no for the preceding --field
          --channel      #channel or ID to send to
          --timestamp    yes to add current timestamp

        Examples:
          !embed --title Hi --description Welcome! --color gold
          !embed --title Stats --field Wins | 42 --inline yes --channel #general
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

        embed = discord.Embed(color=resolve_color(flags.get("color", "blurple")))

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

        if not any([
            flags.get("title"), flags.get("description"), flags.get("image"),
            flags.get("thumbnail"), embed.fields,
        ]):
            return await ctx.send(embed=discord.Embed(
                description="❌ The embed has no content.", color=discord.Color.red()
            ))

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
            await ctx.send(
                embed=discord.Embed(
                    description=f"✅ Embed sent to {channel.mention}.",
                    color=discord.Color.green(),
                ),
                delete_after=5,
            )
        await ctx.message.delete()

    # !embedjson ───────────────────────────────────────────────────────────────

    @commands.command(name="embedjson")
    @commands.has_permissions(manage_messages=True)
    async def embedjson(self, ctx: commands.Context, *, raw_json: str = ""):
        """Send an embed from raw JSON. Usage: !embedjson {"title": "Hi"}"""
        import json, re
        raw_json = re.sub(r"^```(?:json)?\n?", "", raw_json.strip())
        raw_json = re.sub(r"\n?```$", "", raw_json)
        if not raw_json:
            return await ctx.send(embed=discord.Embed(
                description="❌ Provide a JSON object.", color=discord.Color.red()
            ))
        try:
            embed = discord.Embed.from_dict(json.loads(raw_json))
        except Exception as e:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ JSON error: `{e}`", color=discord.Color.red()
            ))
        await ctx.send(embed=embed)
        await ctx.message.delete()

    # !embedcolors ─────────────────────────────────────────────────────────────

    @commands.command(name="embedcolors", aliases=["colors"])
    async def embedcolors(self, ctx: commands.Context):
        """Show all named embed colors."""
        embed = discord.Embed(
            title="🎨 Available Colors",
            description=(
                "Use with `--color` in `!embed`, or type the name / any `#hex` into `/embed`.\n"
                "You can also use any hex code: `#FF5733`"
            ),
            color=discord.Color.blurple(),
        )
        chunk = "\n".join(
            f"`{name:<10}` `#{val:06X}`" for name, val in NAMED_COLORS.items()
        )
        embed.add_field(name="Named Colors", value=chunk, inline=False)
        await ctx.send(embed=embed)

    # Internals ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_flags(tokens: tuple) -> dict:
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
    def _collect_fields(tokens: tuple) -> list:
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
            title="🖼️ Embed Builder Help",
            description=(
                "**Slash (recommended — guided form):**\n`/embed` → fill in the form → "
                "use buttons to add fields, advanced options, then pick a channel to send to.\n\n"
                "**Prefix (power user):**\n"
                "```\n!embed --title Hello --description World --color gold\n```\n"
                "**Flags:** `--title` `--description` `--color` `--footer` `--author` "
                "`--image` `--thumbnail` `--field` `--inline` `--channel` `--timestamp`\n\n"
                "Use `!embedcolors` to see all named colors."
            ),
            color=discord.Color.blurple(),
        )

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        print(f"Embeds cog_app_command_error: {error}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Error: `{error}`", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Error: `{error}`", ephemeral=True)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))
