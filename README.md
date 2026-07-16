# VividForge Bot

A Discord bot built with [discord.py](https://discordpy.readthedocs.io/) featuring moderation tools, utility commands, and fun commands.

## Features

### 🛡️ Moderation
| Command | Description | Permission needed |
|---|---|---|
| `!kick @user [reason]` | Kick a member | Kick Members |
| `!ban @user [reason]` | Ban a member | Ban Members |
| `!unban <user_id>` | Unban a user by ID | Ban Members |
| `!timeout @user <duration> [reason]` | Timeout a member (10s, 5m, 2h, 1d) | Moderate Members |
| `!untimeout @user` | Remove a timeout | Moderate Members |
| `!warn @user [reason]` | Warn a member | Manage Messages |
| `!warnings @user` | View a member's warnings | Manage Messages |
| `!clearwarnings @user` | Clear all warnings for a member | Administrator |
| `!purge <amount>` | Delete up to 100 messages | Manage Messages |
| `!slowmode <seconds>` | Set channel slowmode (0 to disable) | Manage Channels |
| `!lock` | Lock the current channel | Manage Channels |
| `!unlock` | Unlock the current channel | Manage Channels |
| `!nick @user [name]` | Change or reset a member's nickname | Manage Nicknames |

### 🔧 General
| Command | Description |
|---|---|
| `!help [command]` | Show all commands or details about one |
| `!ping` | Check the bot's latency |
| `!uptime` | Show how long the bot has been running |
| `!serverinfo` | Display server information |
| `!userinfo [@user]` | Display user information |
| `!avatar [@user]` | Show a user's avatar |
| `!roleinfo @role` | Display role information |

### 🎲 Fun
| Command | Description |
|---|---|
| `!coinflip` | Flip a coin |
| `!roll [NdN]` | Roll dice (e.g. `!roll 2d6`) |
| `!choose option1 option2 ...` | Let the bot pick an option |
| `!8ball <question>` | Ask the magic 8-ball |

## Setup

### Requirements
- Python 3.11+
- A Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

```bash
# Clone the repo
git clone https://github.com/Maximo1822/Vividforge-Bot.git
cd Vividforge-Bot

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your token
echo "DISCORD_BOT_TOKEN=your_token_here" > .env

# Run the bot
cd bot && python main.py
```

### Discord Developer Portal settings
In your application's **Bot** page, enable:
- ✅ **Message Content Intent** (required for prefix commands)

## Inviting the bot
Generate an invite URL in the Developer Portal with these permissions:
- Kick Members, Ban Members, Moderate Members
- Manage Messages, Manage Channels, Manage Nicknames
- Read Messages / View Channels, Send Messages, Embed Links
