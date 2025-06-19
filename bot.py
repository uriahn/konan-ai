import discord
from openai import OpenAI
import asyncio
import os
from dotenv import load_dotenv

# Loads the API keys
load_dotenv()
DISCORD_API_TOKEN = os.getenv("DISCORD_API_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Defining OpenAI client
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

async def get_ai_response(message_content):
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: openai_client.chat.completions.create(
                model="meta-llama/llama-4-maverick:free", # Just used this cause I felt like it and it's free ¯\_(ツ)_/¯. Also it's moderated but not too censored
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

    if client.user.mentioned_in(message) or message.channel.id == 1307212823356768326 or message.channel.id == 1372374099409502208 or message.channel.id == 1111881291365883984: # TODO: Make this changable in a seperate file
        user_message = message.content

        if client.user.mentioned_in(message):
            user_message = user_message.replace(f'<@{client.user.id}>', '').strip() # Removes the junk from the message

        ai_response = await get_ai_response(user_message) # Send message to AI
        await message.channel.send(ai_response) # Send AI response as a message

client.run(DISCORD_API_TOKEN)
