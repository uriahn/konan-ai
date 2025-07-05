from dotenv import load_dotenv
from openai import OpenAI
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import os
import time

# Load the API keys
load_dotenv()
DISCORD_API_TOKEN = os.getenv("DISCORD_API_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Load the config
import config
BASE_URL = config.BASE_URL
AI_MODEL = config.AI_MODEL
ACTIVE_CHANNELS = config.ACTIVE_CHANNELS
SERVER_ID = config.SERVER_ID
IGNORE_PREFIX = config.IGNORE_PREFIX
SYSTEM_PROMPT = config.SYSTEM_PROMPT
MODEL_NAME = config.MODEL_NAME
MODEL_PRIVACY_POLICIES = config.MODEL_PRIVACY_POLICIES
PERSONALITY = config.PERSONALITY

# Set the logging format
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Define OpenAI client
openai_client = OpenAI(
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# List of past messages and dict of users' nicknames set via /ainame
message_history = []
nicknames = {}


async def get_ai_response(message_history, server_name):
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: openai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "developer", "content": SYSTEM_PROMPT.format(
                             model_name=MODEL_NAME,
                             bot_personality=PERSONALITY,
                             discord_server_name=server_name,
                             current_date_time=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()))},
                          *message_history],
                extra_headers={
                    "HTTP-Referer": "https://github.com/uriahn/konan-ai",
                    "X-Title": "Konan AI",
                }
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.exception(f"Error in getting response:")
        return f"Sorry, the horrible code of my developer caused this error: {str(e)}"


async def send_long_message(channel, message):
    if len(message) <= 2000:
        await channel.send(message)
        return
    
    # Split message into chunks of 2000 characters or less
    chunks = []
    while len(message) > 2000:
        # Find a good break point, those being spaces, newlines, and punctuation
        break_point = 2001
        for chars in (('\n',), ('.', '!', '?'), (';',), (' ',)): # The precedence is \n .!? ; <space>
            if break_point > 2000:
                for i in range(2000, 0, -1):
                    if message[i] in chars:
                        break_point = i + 1
                        break
        if break_point > 2000: break_point = 2000 # Finally, if it failed, break at whatever character
        
        chunks.append(message[:break_point])
        message = message[break_point:]
    
    # Add the remaining message
    if message:
        chunks.append(message)
    
    # Send each chunk
    for i, chunk in enumerate(chunks):
        await channel.send(chunk)


# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="}", intents=intents)


@client.event
async def on_ready():
    # Log if it successfully loaded
    print(f"We have logged in as {client.user}")
    
    # Sync slash commands
    try:
        synced = await client.tree.sync(guild=discord.Object(id=1077552667393527838))
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@client.event
async def on_message(message):
    # Check to make sure that the message wasn't sent by the bot
    if message.author == client.user:
        return

    # Check to make sure you ping it or send it in the right channel
    if client.user.mentioned_in(message) or message.channel.id in ACTIVE_CHANNELS:
        user_message = message.content

        if client.user.mentioned_in(message):
            # Remove the mention from the message
            user_message = user_message.replace(f'<@{client.user.id}>', '').strip()

        if len(user_message) == 0 or user_message.startswith(IGNORE_PREFIX):
            return

        user_nick = message.author.display_name
        if message.author.id in nicknames:
            user_nick = nicknames[message.author.id]

        # Send message to AI
        message_history.append({"role": "user", "content": f"{message.author.display_name}: {user_message}"})
        ai_response = await get_ai_response(message_history, message.guild.name)
        message_history.append({"role": "assistant", "content": ai_response})
        
        try:
            # Send it as multiple messages if needed
            await send_long_message(message.channel, ai_response)
        except Exception as e:
            # Send an error if it doesn't work
            logging.exception(f"Error in sending message:")
            await message.channel.send(f"Sorry, the horrible code of my developer caused this error: {str(e)}")


# Make slash commands
GUILD_ID = discord.Object(id=SERVER_ID)

@client.tree.command(name="info", description="Information about Konan AI", guild=GUILD_ID)
async def infoCmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"""\
Hello! I am Konan AI, a basic AI Discord bot.
I am developed by uriahn and WarpedWartWars on GitHub, and you can view my code at <https://github.com/uriahn/konan-ai>.
My AI model is {MODEL_NAME}.""")

@client.tree.command(name="privacy", description="Our privacy policy", guild=GUILD_ID)
async def privacyCmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"""\
We do not collect any data intentionally. However, we cannot guarantee that your data isn't collected by our providers.
Below are the privacy policies of our provider(s):
{MODEL_PRIVACY_POLICIES}""")

@client.tree.command(name="ainame", description="Set what Konan AI sees your name as", guild=GUILD_ID)
async def ainameCmd(interaction: discord.Interaction, nickname: str):
    if nickname == "":
        del nicknames[interaction.user.id]
        await interaction.response.send_message(
            f"Reset your nickname for Konan AI.", ephemeral=True
        )
    else:
        nicknames[interaction.user.id] = nickname
        await interaction.response.send_message(
            f"Set your nickname for Konan AI to '{nickname}'.", ephemeral=True
        )



client.run(DISCORD_API_TOKEN)
