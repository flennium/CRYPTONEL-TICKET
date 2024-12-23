import discord
from discord import app_commands
from discord.ext import commands
import json

DATABASE_FILE = "data.json"

def load_data():
    with open(DATABASE_FILE, "r") as file:
        return json.load(file)

def save_data(data):
    with open(DATABASE_FILE, "w") as file:
        json.dump(data, file, indent=4)

async def log_action(guild, action, details, user):
    data = load_data()
    log_channel_id = data.get("log_channel")
    if log_channel_id:
        log_channel = guild.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"**{action}** by {user.mention}: {details}")

class RoleManagementModal(discord.ui.Modal, title="Role Management"):
    action = discord.ui.TextInput(label="Action (add/remove)", placeholder="Enter 'add' or 'remove'")
    role_id = discord.ui.TextInput(label="Role ID", placeholder="Enter the role ID")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        action = self.action.value.lower()
        role_id = self.role_id.value

        try:
            role_id = int(role_id)
            if action not in ["add", "remove"]:
                raise ValueError("Invalid action.")
            
            if action == "add":
                if role_id not in data["roles"]:
                    data["roles"].append(role_id)
                    save_data(data)
                    await interaction.response.send_message(f"Role with ID `{role_id}` added to ticket access.", ephemeral=True)
                    await log_action(interaction.guild, "Role Added", f"Role ID `{role_id}` added to ticket access.", interaction.user)
                else:
                    await interaction.response.send_message("Role already has access.", ephemeral=True)
            else:
                if role_id in data["roles"]:
                    data["roles"].remove(role_id)
                    save_data(data)
                    await interaction.response.send_message(f"Role with ID `{role_id}` removed from ticket access.", ephemeral=True)
                    await log_action(interaction.guild, "Role Removed", f"Role ID `{role_id}` removed from ticket access.", interaction.user)
                else:
                    await interaction.response.send_message("Role not found in access list.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid input. Please try again.", ephemeral=True)

class TicketCreationModal(discord.ui.Modal, title="Create Ticket"):
    subject = discord.ui.TextInput(label="Ticket Subject", placeholder="Enter the ticket subject")
    description = discord.ui.TextInput(label="Description", placeholder="Enter the ticket description", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        guild = interaction.guild
        category_id = data.get("ticket_category")
        roles = data.get("roles", [])
        blacklist = data.get("blacklist", [])
        
        if int(interaction.user.id) in blacklist:
            await interaction.response.send_message("You are blacklisted and cannot open a ticket.", ephemeral=True)
            return

        category = discord.utils.get(guild.categories, id=category_id)
        if not category:
            await interaction.response.send_message("Ticket category is not set or invalid. Please configure it first.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
        }
        
        for role_id in roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            reason="New ticket created",
        )

        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        
        await log_action(interaction.guild, "**New ticket created**", f"by {interaction.user.mention}:\nSubject: {self.subject.value}\nDescription: {self.description.value}", interaction.user)


class BlacklistManagementModal(discord.ui.Modal, title="Blacklist Management"):
    action = discord.ui.TextInput(label="Action (add/remove)", placeholder="Enter 'add' or 'remove'")
    user_id = discord.ui.TextInput(label="User ID", placeholder="Enter the user ID")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        action = self.action.value.lower()
        user_id = self.user_id.value

        try:
            user_id = int(user_id)
            if action not in ["add", "remove"]:
                raise ValueError("Invalid action.")

            if action == "add":
                if user_id not in data["blacklist"]:
                    data["blacklist"].append(user_id)
                    save_data(data)
                    await interaction.response.send_message(f"User with ID `{user_id}` added to the blacklist.", ephemeral=True)
                    await log_action(interaction.guild, "User Blacklisted", f"User ID `{user_id}` added to the blacklist.", interaction.user)
                else:
                    await interaction.response.send_message("User is already blacklisted.", ephemeral=True)
            else:
                if user_id in data["blacklist"]:
                    data["blacklist"].remove(user_id)
                    save_data(data)
                    await interaction.response.send_message(f"User with ID `{user_id}` removed from the blacklist.", ephemeral=True)
                    await log_action(interaction.guild, "User Removed from Blacklist", f"\n**User ID** `{user_id}` removed from the blacklist.", interaction.user)
                else:
                    await interaction.response.send_message("User not found in the blacklist.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid input. Please try again.", ephemeral=True)

class LogsConfigurationModal(discord.ui.Modal, title="Logs Configuration"):
    channel_id = discord.ui.TextInput(label="Channel ID", placeholder="Enter the channel ID for logs")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        try:
            channel_id = int(self.channel_id.value)
            data["log_channel"] = channel_id
            save_data(data)
            await interaction.response.send_message(f"Logs will be sent to channel ID `{channel_id}`.", ephemeral=True)
            
            await log_action(interaction.guild, "Log Channel Configured", f"Log channel set to ID `{channel_id}`.", interaction.user)
        except ValueError:
            await interaction.response.send_message("Invalid channel ID. Please try again.", ephemeral=True)

class TicketSystemDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Role Management", description="Manage roles for ticket access."),
            discord.SelectOption(label="Ticket Creation", description="Open a ticket creation form."),
            discord.SelectOption(label="Blacklist Management", description="Manage blacklisted users."),
            discord.SelectOption(label="Logs Configuration", description="Set up logging for tickets."),
        ]
        super().__init__(
            placeholder="Select an option...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]

        if selected_option == "Role Management":
            await interaction.response.send_modal(RoleManagementModal())
        elif selected_option == "Ticket Creation":
            await interaction.response.send_modal(TicketCreationModal())
        elif selected_option == "Blacklist Management":
            await interaction.response.send_modal(BlacklistManagementModal())
        elif selected_option == "Logs Configuration":
            await interaction.response.send_modal(LogsConfigurationModal())
        else:
            await interaction.response.send_message("Unknown option selected.", ephemeral=True)

class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSystemDropdown())

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="t-system", description="Manage the Ticket System")
    async def t_system(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Ticket System Management",
            description="Select an option below to manage the ticket system.",
            color=discord.Color.blue(),
        )
        view = TicketSystemView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
