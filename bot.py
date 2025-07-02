from dotenv import load_dotenv
from openai import OpenAI
import discord
import asyncio
import logging
import os
import sys
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

# Set the logging format
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Define OpenAI client
openai_client = OpenAI(
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY
)


async def get_ai_response(message_content):
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: openai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": message_content}],
                extra_headers={
                    "HTTP-Referer": "https://github.com/uriahn/konan-ai",
                    "X-Title": "Konan AI",
                }
            )
        )
        return response.choices[0].message.content
    except Exception as e:
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


# Initialize Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    # Log if it successfully loaded
    print(f"We have logged in as {client.user}")


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

        if len(user_message) == 0:
            return

        # Send message to AI
        ai_response = await get_ai_response(user_message)
        
        try:
            # Send it as multiple messages if needed
            await send_long_message(message.channel, ai_response)
        except Exception as e:
            # Send an error if it doesn't work
            logging.exception(f"Error in sending message:")
            await message.channel.send(f"Sorry, the horrible code of my developer caused this error: {str(e)}")


client.run(DISCORD_API_TOKEN)
