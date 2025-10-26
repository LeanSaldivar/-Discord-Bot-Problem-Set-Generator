import discord
from discord.ext import commands

import logging

from dotenv import load_dotenv
import os

import api
import aiohttp

import plot

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
async def chat(ctx, *, content: str):
    """Multi-turn conversation - maintains history per user."""
    try:
        await ctx.typing()
        session_id = str(ctx.channel.id)  # Each user has their own conversation
        response = api.send_message(session_id, content)
        await send_as_chunks(ctx, response.text)

        await process_latex_response(ctx, response)

        print(f"Successfully responded to !chat for user {ctx.author.name}: {content}")
    except Exception as e:
        print(f"An error occurred in chat: {e}")
        await ctx.send("An error occurred while processing your request.")


@bot.command()
async def chat_with_file(ctx, *, content: str):
    """Multi-turn conversation with file attachment - maintains history per user."""
    if not ctx.message.attachments:
        await ctx.send("Please attach an image or PDF file.")
        return

    attachment = ctx.message.attachments[0]
    mime_type = attachment.content_type

    allowed_types = ["image/png", "application/pdf", "image/jpeg", "image/jpg"]
    if mime_type not in allowed_types:
        await ctx.send(f"Unsupported file type: `{mime_type}`. Only PNG, JPG, and PDF are allowed.")
        return

    try:
        await ctx.typing()
        session_id = str(ctx.author.id)

        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    await ctx.send("Could not download the file.")
                    return
                file_bytes = await resp.read()

        response = api.send_message_with_file(session_id, content, file_bytes, mime_type)
        await send_as_chunks(ctx, response.text)

        await process_latex_response(ctx, response)

        print(f"Successfully responded to !chat_with_file for user {ctx.author.name}: {content}")
    except Exception as e:
        print(f"An error occurred in chat_with_file: {e}")
        await ctx.send("An error occurred while processing your request.")

async def process_latex_response(ctx, response):
    # Extract and render all LaTeX equations if present
    latex_equations = plot.extract_latex(response.text)
    if latex_equations:
        try:
            image_buffer = plot.render_all_latex_to_image(latex_equations)
            if image_buffer:
                await ctx.send(file=discord.File(fp=image_buffer, filename="equations.png"))
        except Exception as latex_error:
            print(f"Failed to render LaTeX: {latex_error}")

@bot.command()
async def clear_chat(ctx):
    """Clear your conversation history."""
    session_id = str(ctx.author.id)
    cleared = api.clear_session(session_id)
    if cleared:
        await ctx.send("✅ Your conversation history has been cleared!")
    else:
        await ctx.send("You don't have an active conversation.")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)