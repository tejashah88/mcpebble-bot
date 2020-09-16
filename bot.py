import os
import signal
import asyncio
from dotenv import load_dotenv
load_dotenv()

import discord
BOT_TOKEN = os.getenv('BOT_TOKEN')

from periodic import Periodic
from mcstatus import MinecraftServer
SERVER_IP = os.getenv('SERVER_IP')
mc_server = MinecraftServer.lookup(SERVER_IP)

MAINTENANCE_MOTD = os.getenv('MAINTENANCE_MOTD')

bot = discord.Client()

async def update_status():
    try:
        mc_status = mc_server.status()
        online_ppl = mc_status.players.online
        max_ppl = mc_status.players.max
        motd = mc_status.description['extra'][0]['text']

        if MAINTENANCE_MOTD == motd:
            status = discord.Status.do_not_disturb
            status_msg = f'Under maintenance!'
        else:
            status = discord.Status.online
            status_msg = f'Online: {online_ppl}/{max_ppl} players!'
    except:
        status_msg = 'Offline'

    await bot.change_presence(
        status=status,
        activity=discord.Game(status_msg)
    )


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


# Source: https://www.roguelynn.com/words/asyncio-graceful-shutdowns/
async def shutdown(signal, loop):
    await cron.stop()
    await bot.change_presence(status=discord.Status.invisible)
    await bot.logout()
    print('Logged out!')

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    print(f'Cancelling {len(tasks)} outstanding tasks')
    await asyncio.gather(*tasks, return_exceptions=True)

    loop.stop()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    cron = Periodic(5, update_status)

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for signal in signals:
        signal_handler_fn = lambda signal=signal: asyncio.create_task(shutdown(signal, loop))
        loop.add_signal_handler(signal, signal_handler_fn)

    print('Initializing bot...')
    try:
        loop.create_task(cron.start())
        loop.create_task(bot.start(BOT_TOKEN))
        loop.run_forever()
    finally:
        loop.close()
