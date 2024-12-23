import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="flennnuwu", intents=intents)

async def load_cogs():
    for folder in ["commands", "events"]:
        for filename in os.listdir(f"./{folder}"):
            if filename.endswith(".py") and not filename.startswith("__"):
                await bot.load_extension(f"{folder}.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


TOKEN = "MTEwMjkwNTIwODI5MzU3MjYwOA.Gf4dTG.lB1wLH4H4DHmL7REcI4OMiTohnYitS1a9uf0jw"
bot.run(TOKEN)



