import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import discord
BOT_TOKEN = os.getenv('BOT_TOKEN')

from periodic import Periodic
from mcstatus import MinecraftServer
SERVER_IP = os.getenv('SERVER_IP')
mc_server = MinecraftServer.lookup(SERVER_IP)

loop = asyncio.get_event_loop()

bot = discord.Client()

async def update_status():
    try:
        mc_status = mc_server.status()
        online_ppl = mc_status.players.online
        max_ppl = mc_status.players.max

        status = f'Online: {online_ppl}/{max_ppl} players!'
    except:
        status = 'Offline'

    game = discord.Game(status)
    await bot.change_presence(status=discord.Status.online, activity=game)


@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    await update_status()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.strip() in ['!whodis', '!playing', '!status']:
        try:
            mc_status = mc_server.status()
            mc_query = mc_server.query()

            online_ppl = mc_status.players.online
            max_ppl = mc_status.players.max
            players = mc_query.players.names

            main_status = f'**online** with {online_ppl}/{max_ppl} players'
            if online_ppl > 0:
                main_status += ':\n' + '\n'.join([f'{i + 1}. {player}' for (i, player) in enumerate(players)])
            else:
                main_status += '!'
        except Exception as ex:
            main_status = '**offline**!'

        await message.channel.send(f'The server is {main_status}')


if __name__ == '__main__':
    cron = Periodic(5, update_status)

    # Shamelessly copied from https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.run
    # HACK: Probably shouldn't be spamming `loop.run_until_complete`!
    print('Initializing bot...')
    try:
        loop.run_until_complete(cron.start())
        loop.run_until_complete(bot.start(BOT_TOKEN))
    except KeyboardInterrupt:
        loop.run_until_complete(bot.change_presence(status=discord.Status.invisible))
        loop.run_until_complete(bot.logout())
        loop.run_until_complete(cron.stop())
        print('Logged out!')
    finally:
        loop.close()
