import discord
from openai import OpenAI
import asyncio
import os
from dotenv import load_dotenv

# Loads the API keys
load_dotenv()
DISCORD_API_TOKEN = os.getenv("DISCORD_API_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Loading the config
import config
BASE_URL = config.BASE_URL
AI_MODEL = config.AI_MODEL
ACTIVE_CHANNELS = config.ACTIVE_CHANNELS

# Defining OpenAI client
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
    while len(message) > 2000: # Find a good break point, those being spaces, newlines, and punctuation
        break_point = 2000
        for i in range(1999, 1800, -1):
            if message[i] in [' ', '\n', '.', '!', '?', ';']:
                break_point = i + 1
                break
        
        chunks.append(message[:break_point])
        message = message[break_point:]
    
    # Add the remaining message
    if message:
        chunks.append(message)
    
    # Send each chunk
    for i, chunk in enumerate(chunks):
        if i == 0:
            await channel.send(chunk)
        else:
            await channel.send(f"(continued...)\n{chunk}")

# Just some basic Discord loading stuff
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}") # Logs if it successfully loaded

# Checks to make sure you ping it or send it in the right channel
@client.event
async def on_message(message):
    if message.author == client.user: # Checks to make sure that the message wasn't sent by the bot
        return

    if client.user.mentioned_in(message) or message.channel.id in ACTIVE_CHANNELS:
        user_message = message.content

        if client.user.mentioned_in(message):
            user_message = user_message.replace(f'<@{client.user.id}>', '').strip() # Removes the junk from the message

        if len(user_message) == 0:
            return

        ai_response = await get_ai_response(user_message) # Send message to AI
        
        try:
            await send_long_message(message.channel, ai_response) # Send it as multiple messages
        except Exception as e:
            await message.channel.send(f"Sorry, the horrible code of my developer caused this error: {str(e)}") # Sends an error if it doens't work

client.run(DISCORD_API_TOKEN)
