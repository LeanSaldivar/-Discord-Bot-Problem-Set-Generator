import discord
from discord.ext import commands

import logging

from dotenv import load_dotenv
import os

import api
import aiohttp

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def send_as_chunks(ctx, text):
    """Splits text into 2000-character chunks and sends them as separate messages."""
    if not text:
        return
    for i in range(0, len(text), 2000):
        await ctx.send(text[i:i+2000])

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command()
async def gen_prob(ctx, *, content: str):
    try:
        await ctx.typing()
        response = api.generate(content)
        await send_as_chunks(ctx, response.candidates[0].content.parts[0].text)
        print(f"Successfully responded to !gen_prob for: {content}")
    except Exception as e:
        print(f"An error occurred in gen_prob: {e}")
        await ctx.send("An error occurred while processing your request.")

@bot.command()
async def generate_prob_img(ctx, *, content: str):
    if not ctx.message.attachments:
        await ctx.send("Please attach an image or PDF file.")
        return

    attachment = ctx.message.attachments[0]
    mime_type = attachment.content_type

    # Accept only PNG or PDF
    allowed_types = ["image/png", "application/pdf"]
    if mime_type not in allowed_types:
        await ctx.send(f"Unsupported file type: `{mime_type}`. Only PNG and PDF are allowed.")
        return

    try:
        await ctx.typing()
        # Download file bytes
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    await ctx.send("Could not download the file.")
                    return
                file_bytes = await resp.read()

        # Send to Gemini
        response = api.generate_with_file(content, file_bytes, mime_type)

        # Send back Gemini response
        await send_as_chunks(ctx, response.candidates[0].content.parts[0].text)
        print(f"Successfully responded to !generate_prob_img for: {content}")
    except Exception as e:
        print(f"An error occurred in generate_prob_img: {e}")
        await ctx.send("An error occurred while processing your request.")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
