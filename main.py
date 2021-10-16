import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

import artifacts
import companion
import helpers
import ratings

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_NUDE_CHANNEL_NAME = os.getenv('DISCORD_NUDE_CHANNEL_NAME')

intents = discord.Intents.default()
intents.members = True  # Subscribe to the privileged members intent.
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name != DISCORD_NUDE_CHANNEL_NAME:
        return

    user_url = message.content
    error, validated_url = helpers.get_validated_user_url(user_url)
    if error is not None:
        if error == helpers.NOT_VALID_URL_ERROR:
            return
        await message.reply(f'`{error}`', mention_author=True)
        return

    reply = ''

    art_block = artifacts.get_block(validated_url)
    reply += ':safety_vest: **АРТЕФАКТЫ** :safety_vest:\n'
    reply += art_block
    reply += '\n'

    ratings_block = ratings.get_block(validated_url)
    reply += ':first_place: **РЕЙТИНГИ** :first_place:\n'
    reply += ratings_block
    reply += '\n'

    companion_block = companion.get_block(validated_url)
    reply += ':space_invader: **ТЕНЬ** :space_invader:\n'
    reply += companion_block
    reply += '\n'

    await message.reply(reply, mention_author=True)


bot.run(TOKEN)
