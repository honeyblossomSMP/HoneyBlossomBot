# HoneyBlossomBot

A Discord bot for managing Minecraft server interactions, player warps, and support requests.

## Features

- **Player Warp Requests**: Players can request new warps with coordinates and purpose
- **Support Tickets**: General support request system for players
- **RCON Integration**: Direct communication with Minecraft server via RCON
- **Discord Integration**: Full Discord.py slash commands and modal support
- **Staff Management**: Role-based staff operations and logging

## Requirements

- Python 3.8+
- Discord.py
- aio-mc-rcon
- python-dotenv

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/HoneyBlossomBot.git
   cd HoneyBlossomBot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```env
   DISCORD_TOKEN=your_discord_bot_token
   MC_IP=your_minecraft_server_ip
   RCON_PORT=27487
   RCON_PASS=your_rcon_password
   ```

## Configuration

Update the following IDs in `main.py` with your server's channel and role IDs:

- `STAFF_ROLE_ID`: Staff role ID
- `TICKET_CATEGORY_ID`: Category for support tickets
- `LOG_CHANNEL_ID`: Logging channel
- `WELCOME_CHANNEL_ID`: Welcome channel
- `RULES_CHANNEL_ID`: Rules channel
- `SUPPORT_TICKET_CHANNEL_ID`: Support ticket channel
- `VERIFICATION_CHANNEL_ID`: Verification channel
- `ADMIN_CHAT_CHANNEL_ID`: Admin chat channel
- `ANNOUNCEMENT_CHANNEL_ID`: Announcements channel

## Running the Bot

```bash
python main.py
```

## Deployment

This bot is configured for Heroku deployment using the included `Procfile`.

To deploy:
```bash
heroku create your-app-name
heroku config:set DISCORD_TOKEN=your_token MC_IP=your_ip RCON_PORT=27487 RCON_PASS=your_password
git push heroku main
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please open an GitHub issue.
