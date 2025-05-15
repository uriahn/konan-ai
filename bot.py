import discord
from openai import OpenAI
import asyncio
import os
from dotenv import load_dotenv

# Loads the API keys
load_dotenv()
DISCORD_API_TOKEN = os.getenv("DISCORD_API_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
    if client.user.mentioned_in(message) or message.channel.id == 1111881291365883984: #TODO: Make this changable in a seperate file
        await message.channel.send("It works!")

client.run(DISCORD_API_TOKEN)

# Defining OpenAI stuff
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Sending message to the AI
completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "https://github.com/uriahn/konan-ai",
        "X-Title": "Konan AI",
    },
    model="meta-llama/llama-4-maverick:free", # Just used this cause I felt like it and it's free ¯\_(ツ)_/¯. Also it's moderated but not too censored
        messages=[
        {
            "role": "user",
            "content": "This will be a variable eventually, haven't added the messages yet"
        }
    ]
)
