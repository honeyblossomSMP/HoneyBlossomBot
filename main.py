import discord
from discord import app_commands
from discord.ext import commands
import aiomcrcon
import asyncio
import os 
import re 
from dotenv import load_dotenv 

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MC_IP = os.getenv("MC_IP")
RCON_PORT = int(os.getenv("RCON_PORT", 27487)) 
RCON_PASS = os.getenv("RCON_PASS")

# Configuration Constants
STAFF_ROLE_ID = 1460783467443786032
TICKET_CATEGORY_ID = 1461434472460324874 
LOG_CHANNEL_ID = 1461441930629222473 
WELCOME_CHANNEL_ID = 1461793986795671613 
RULES_CHANNEL_ID = 1459116888444506194 
SUPPORT_TICKET_CHANNEL_ID = 1461434607072317594 
VERIFICATION_CHANNEL_ID = 1459372997918851173
ADMIN_CHAT_CHANNEL_ID = 1460396224548049052

# --- MODALS ---

class WarpModal(discord.ui.Modal, title="Player Warp Request"):
    warp_name = discord.ui.TextInput(label="Warp Name", placeholder="e.g. Grinder, Library", required=True)
    location = discord.ui.TextInput(label="Location (Coordinates)", placeholder="X: 100, Y: 64, Z: -200", required=True)
    purpose = discord.ui.TextInput(label="Purpose of Warp", style=discord.TextStyle.paragraph, placeholder="Explain what this warp is for...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = f"**Warp Name:** {self.warp_name.value}\n**Location:** {self.location.value}\n**Purpose:** {self.purpose.value}"
        view = RequestLauncher()
        await view.create_request(interaction, "warp", info, already_deferred=True)

class SupportModal(discord.ui.Modal, title="General Support Request"):
    subject = discord.ui.TextInput(label="Subject", placeholder="Briefly describe the issue", required=True)
    details = discord.ui.TextInput(label="Details", style=discord.TextStyle.paragraph, placeholder="What do you need help with?", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = f"**Subject:** {self.subject.value}\n**Details:** {self.details.value}"
        view = RequestLauncher()
        await view.create_request(interaction, "support", info, already_deferred=True)

class WhitelistModal(discord.ui.Modal, title="Whitelist Application"):
    username = discord.ui.TextInput(label="Minecraft Username", placeholder="Exactly as it appears in-game", required=True)
    platform = discord.ui.TextInput(label="Platform", placeholder="Java or Bedrock?", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = f"**MC Username:** {self.username.value}\n**Platform:** {self.platform.value}"
        view = RequestLauncher()
        await view.create_request(interaction, "whitelist", info, already_deferred=True)

class StaffAppModal(discord.ui.Modal, title="Staff Application"):
    role = discord.ui.TextInput(label="Role Applying For", placeholder="Honey Lotus, Adminbeestrator, or Hive Overseer", required=True)
    reason = discord.ui.TextInput(label="Why do you want this role?", style=discord.TextStyle.paragraph, required=True)
    experience = discord.ui.TextInput(label="Experience", style=discord.TextStyle.paragraph, placeholder="Tell us about your history as staff...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = f"**Role Applied For:** {self.role.value}\n**Reasoning:** {self.reason.value}\n**Experience:** {self.experience.value}"
        # Staff apps use the same logic but a different prefix
        view = RequestLauncher() 
        await view.create_request(interaction, "staff-app", info, already_deferred=True)

# --- VIEWS ---

class TicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("💾 Archiving and closing...")
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        log_content = f"--- Log: {interaction.channel.name} ---\nClosed by: {interaction.user.name}\n\n"
        async for message in interaction.channel.history(limit=200, oldest_first=True):
            timestamp = message.created_at.strftime('%Y-%m-%d %H:%M')
            log_content += f"[{timestamp}] {message.author}: {message.content}\n"
        
        file_path = f"log_{interaction.channel.id}.txt"
        with open(file_path, "w", encoding="utf-8") as f: f.write(log_content)
        
        if log_channel:
            try:
                embed = discord.Embed(title="Channel Archived", description=f"**Name:** {interaction.channel.name}", color=discord.Color.red())
                await log_channel.send(embed=embed, file=discord.File(file_path, filename=f"{interaction.channel.name}.txt"))
            except Exception as e: print(f"Logging failed: {e}")
        
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass
        if os.path.exists(file_path): os.remove(file_path)

class RequestLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_request(self, interaction: discord.Interaction, prefix, welcome_msg, already_deferred=False):
        if not already_deferred:
            await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)
        
        if not category: 
            return await interaction.followup.send("Category not found!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(name=f"{prefix}-{interaction.user.name}", category=category, overwrites=overwrites)
        await interaction.followup.send(f"✅ Created! {channel.mention}", ephemeral=True)

        embed = discord.Embed(title=f"{prefix.upper()} Request", description=f"Hello {interaction.user.mention}!\n\n{welcome_msg}", color=discord.Color.blue())
        await channel.send(content=f"<@&{STAFF_ROLE_ID}>", embed=embed, view=TicketControl())

    @discord.ui.button(label="General Support", style=discord.ButtonStyle.primary, custom_id="req_support", emoji="🛠️")
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SupportModal())

    @discord.ui.button(label="Whitelist Request", style=discord.ButtonStyle.success, custom_id="req_whitelist", emoji="📝")
    async def whitelist_req(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistModal())

    @discord.ui.button(label="Player Warp Request", style=discord.ButtonStyle.secondary, custom_id="req_warp", emoji="📍")
    async def player_warp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarpModal())

class StaffAppLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Staff", style=discord.ButtonStyle.danger, custom_id="staff_apply_btn", emoji="🐝")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StaffAppModal())

# --- BOT SETUP & EVENTS ---

class WhitelistBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register persistent views
        self.add_view(RequestLauncher())
        self.add_view(TicketControl())
        self.add_view(StaffAppLauncher())
        
        self.loop.create_task(self.server_watchdog())
        await self.tree.sync()
        print(f"✅ Bot is ready!")

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title=f"🌸 Welcome to Honey Blossom, {member.display_name}!",
                description=(
                    f"Hi {member.mention}! To get started on the SMP, please follow these steps:\n\n"
                    f"✅ **Verify Age:** Refer to <#{VERIFICATION_CHANNEL_ID}> to confirm you are 18+.\n"
                    f"✅ **Read Rules:** Please check <#{RULES_CHANNEL_ID}> and react with a ✅.\n"
                    f"✅ **Join:** Go to <#{SUPPORT_TICKET_CHANNEL_ID}> and click **Whitelist Request**.\n\n"
                    f"*Make sure to mention if you are on Bedrock or Java in your ticket!*"
                ),
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Honey Blossom SMP • Automation by MusicalCube")
            try: await channel.send(content=f"Welcome {member.mention}!", embed=embed)
            except: print("❌ Failed to send welcome message.")

    async def server_watchdog(self):
        await self.wait_until_ready()
        fail_count = 0
        alert_dispatched = False
        while not self.is_closed():
            try:
                client = aiomcrcon.Client(MC_IP, RCON_PORT, RCON_PASS)
                await asyncio.wait_for(client.connect(), timeout=5.0)
                await client.send_cmd("list")
                await client.close()
                fail_count = 0
                alert_dispatched = False
            except Exception:
                fail_count += 1
                if fail_count >= 5 and not alert_dispatched:
                    chan = self.get_channel(ADMIN_CHAT_CHANNEL_ID)
                    if chan:
                        await chan.send(f"🚨 **EMERGENCY:** <@&{STAFF_ROLE_ID}> The server has been unreachable for 5 minutes!")
                        alert_dispatched = True
            await asyncio.sleep(60)

bot = WhitelistBot()

# --- COMMANDS ---

@bot.tree.command(name="setup-requests", description="Deploys the request system (Staff Only)")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def setup_requests(interaction: discord.Interaction):
    embed = discord.Embed(title="Server Request Center", description="Select a button below to open a ticket.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=RequestLauncher())
    await interaction.response.send_message("Deployed!", ephemeral=True)

@bot.tree.command(name="setup-staff-apps", description="Deploys the Staff Application system (Staff Only)")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def setup_staff(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Staff Recruitment", 
        description="We are looking for dedicated members to join our team as Honey Lotus, Adminbeestrator, or Hive Overseer!", 
        color=discord.Color.red()
    )
    await interaction.channel.send(embed=embed, view=StaffAppLauncher())
    await interaction.response.send_message("Staff app center deployed!", ephemeral=True)

@bot.tree.command(name="players", description="Shows the online players")
async def players(interaction: discord.Interaction):
    await interaction.response.defer() 
    try:
        client = aiomcrcon.Client(MC_IP, RCON_PORT, RCON_PASS)
        await client.connect()
        raw_response, _ = await client.send_cmd("list")
        await client.close()
        # Cleaning logic
        clean_text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', raw_response)
        clean_text = re.sub(r'§[0-9a-fk-orx]', '', clean_text, flags=re.IGNORECASE)
        single_line = " ".join(clean_text.splitlines())
        count_match = re.search(r'(\d+ out of maximum \d+)', single_line)
        header = count_match.group(1) + " players online." if count_match else "Server Status"
        
        embed = discord.Embed(title="🏰 Honey Blossom SMP Status", description=f"**{header}**", color=discord.Color.gold())
        embed.set_footer(text=f"IP: {MC_IP}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Connection Error: {e}", ephemeral=True)

@bot.tree.command(name="whitelist", description="Add a player to the server")
@app_commands.checks.has_role(STAFF_ROLE_ID) 
async def whitelist(interaction: discord.Interaction, username: str, platform: str):
    cmd = f"fwhitelist add {username}" if platform.lower() == "bedrock" else f"whitelist add {username}"
    await interaction.response.defer()
    try:
        client = aiomcrcon.Client(MC_IP, RCON_PORT, RCON_PASS)
        await client.connect()
        response, _ = await client.send_cmd(cmd)
        await client.close()
        await interaction.followup.send(f"**Sent:** `{cmd}`\n**Response:** `{response}`")
    except Exception as e: await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="msg", description="Send a private message to a player in-game")
async def msg(interaction: discord.Interaction, mc_username: str, message: str):
    sender = interaction.user.display_name
    mc_cmd = (f'tellraw {mc_username} ["", {{"text":"[Discord] ","color":"gray"}}, {{"text":"{sender}","color":"gold"}}, {{"text":": ","color":"white"}}, {{"text":"{message}","color":"white"}}]')
    await interaction.response.defer(ephemeral=True)
    try:
        client = aiomcrcon.Client(MC_IP, RCON_PORT, RCON_PASS)
        await client.connect()
        await client.send_cmd(mc_cmd)
        await client.close()
        await interaction.followup.send(f"📬 Message sent to **{mc_username}**!", ephemeral=True)
    except Exception as e: await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

bot.run(TOKEN)