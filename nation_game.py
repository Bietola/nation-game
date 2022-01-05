from telegram.ext import CommandHandler, ConversationHandler, MessageHandler
from telegram.ext.filters import Filters
import random
import re
from pathlib import Path
from collections import defaultdict
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from result import Result, Ok, Err
import time
import atomics
import threading

import emoji_utils as emjutl

# Globals
g_chosen_flag = {}

# Game states
RECV_ANS = range(1)

g_db = {}
g_db['players'] = defaultdict(
    lambda: {'tot_points': 0, 'points': 0},
    json.loads(Path('./assets/players.json').open().read())
)
g_db['world'] = json.loads(Path('./assets/world.json').open().read())

def db(field):
    global g_db
    return g_db[field]

def flush_db(field):
    global g_db
    Path(f'./assets/{field}.json').write_text(
        json.dumps(g_db[field], indent=4),
        encoding="utf-8"
    )

# Extract name of flag from flag emoji
def extract_flag_name(flag_emoji_full_name):
    return extract_flag_name.re.match(flag_emoji_full_name).group(1)

extract_flag_name.re = re.compile(r'^flag:\s(.*)$')

# 1 round of the game (record win)
#
# EXAMPLE:
# /ng start
# > Ok
# > :flag_italy:
# France
# > No, 9 guesses left for Chicco
# Italy
# > Davide wins! 10 wood, 2 bronze victories in all
def start_round(upd, ctx):
    def send_txt(txt):
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=txt
        )

    send_txt('Let the game commence')

    global g_chosen_flag
    g_chosen_flag = random.choice(
        list(filter(lambda e: 'flag' in e['name'], emjutl.db())))
    send_txt(g_chosen_flag['emoji'])

    return RECV_ANS

def receive_ans(upd, ctx):
    user = upd.message.from_user

    if upd.message.text.lower() == 'ranking':
        upd.message.reply_text(json.dumps(db('players'), indent=4))
        return RECV_ANS

    elif upd.message.text.lower() == 'cheat':
        upd.message.reply_text(f'answer: {g_chosen_flag["name"]}')
        return RECV_ANS

    elif upd.message.text.lower() == 'cancel':
        upd.message.reply_text(f'No more (answer: {g_chosen_flag["name"]})')
        return ConversationHandler.END

    elif upd.message.text.lower() == extract_flag_name(g_chosen_flag['name']).lower():
        winner_data = db('players')[user.username]
        tot_points = winner_data['tot_points']
        points = winner_data['points']

        upd.message.reply_text(
            f'{user.name} is the winner [{points + 1}/{tot_points + 1}]'
        )

        # Record win
        winner_data['points'] += 1
        winner_data['tot_points'] += 1

        return ConversationHandler.END

    else:
        upd.message.reply_text(f'{user.name}, you are wrong D:')
        return RECV_ANS

def cancel_round(upd, ctx):
    return ConversationHandler.END

def print_world_map():
    df = pd.DataFrame.from_dict(
        db('world')
    )

    fig = px.choropleth(
        df,
        locations='Country Code',
        color='Price',
        hover_name='Country Name',
        title='World Map',
        color_continuous_scale=px.colors.sequential.PuRd
    )

    map_path = Path(__file__).parent / 'assets/cache/world-map.png'
    fig.write_image(map_path)

    return map_path

def show_world_map(upd, ctx):
    map_path = print_world_map()

    ctx.bot.send_photo(
        chat_id=upd.effective_chat.id,
        photo=map_path.open('rb')
    )

def save_game(upd, ctx):
    flush_db('players')
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text='Player data saved'
    )

    flush_db('world')
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text='World map saved'
    )

def find_nation(world, nation_code):
    nation = filter(
        lambda nat: nat['Country Code'] == nation_code,
        world
    )
    nation = next(nation, None)

    if not nation:
        return Err(f'{nation_code} is not a valid nation code')

    return Ok(nation)


def find_army(world, nation, owner):
    nation = find_nation(world, nation)
    if isinstance(nation, Err):
        return nation
    nation = nation.value
    
    armies = nation.get('Armies', [])

    army = filter(
        lambda army: army['Owner'] == owner,
        armies
    )
    army = next(army, None)
    if not army:
        armies.append({'Owner': owner, 'Strength': 0, 'Fighting': []})
        army = armies[-1]

    return Ok(army)

def deploy_army(admin=False):
    def handler(upd, ctx):
        if len(ctx.args) < 2:
            upd.message.reply_text(
                'Usage: `/dep NATION_CODE AMOUNT [+/-OPPONENTS]`'
            )
            return

        nation_code = ctx.args[0]
        amount = int(ctx.args[1])
        off_opts = ctx.args[2:]
        owner = upd.message.from_user.username

        world = db('world')
        players = db('players')

        if not admin and amount > players[owner]['points']:
            upd.message.reply_text(
                f'Not enough points ({players[owner]["points"]} < {amount})'
            )
            return

        # NB. This creates an empty army if there isn't one
        army = find_army(world, nation_code, owner)
        if isinstance(army, Err):
            upd.message.reply_text(
                army.value
            )
            return
        army = army.value

        army['Strength'] += amount
        players[owner]['points'] -= amount

        res = apply_offensive_opts(owner, nation_code, off_opts)
        if isinstance(res, Err):
            upd.message.reply_text(res.value)

        upd.message.reply_text('Sucessfuly deployed')

    return handler

def apply_offensive_opts(offender, nation, opts):
    world = db('world')

    # NB. This creates an empty army if there isn't one
    army = find_army(world, nation, offender)
    if isinstance(army, Err):
        return army
    army = army.value

    for opt in opts:
        if opt[0] == '-':
            opp = opt[1:]
            if opp in army['Fighting']:
                army['Fighting'].remove(opp)
            else:
                return Err(f'ERR: Not fighting {opp}')
        else:
            opp = opt
            if opp in army['Fighting']:
                return Err(f'ERR: Already fighting {opp}')
            else:
                army['Fighting'].append(opp)
    
    return Ok()

def begin_offensive(upd, ctx):
    if len(ctx.args) < 2:
        upd.message.reply_text(
            'Usage: `/att NATION_CODE [+/-OPPONENTS]`'
        )
        return

    nation = ctx.args[0]
    opts = ctx.args[1:]
    owner = upd.message.from_user.username

    res = apply_offensive_opts(owner, nation, opts)
    if isinstance(res, Err):
        upd.message.reply_text(res.value)
    else:
        upd.message.reply_text('Offensive plan executed')

def show_nation_info(upd, ctx):
    if len(ctx.args) != 1:
        upd.message.reply_text(
            'Usage: nati NATION_CODE'
        )
        return

    nation_code = ctx.args[0]

    world = db('world')

    res = find_nation(world, nation_code)
    if isinstance(res, Err):
        upd.message.reply_text(res.value)
    nation = res.value

    upd.message.reply_text(json.dumps(nation, indent=4))

def monitor_armies(upd, ctx):
    if len(ctx.args) < 1:
        upd.message.reply_text(
            'Usage: mon <STOP|NATION_CODE> [UPDATE_SECS=30]'
        )
        return

    nation_code = ctx.args[0]
    update_secs = int(ctx.args[1]) if len(ctx.args) > 1 else 30

    owner = upd.message.from_user
    username = owner.username
    threads = monitor_armies.threads

    if nation_code == 'STOP':
        threads[username][1].store(1)
        threads[username][0].join()
        threads.pop(username)
        return

    world = db('world')

    res = find_nation(world, nation_code)
    if isinstance(res, Err):
        upd.message.reply_text(res.value)
    nation = res.value

    def monitor():
        while True:
            # TODO/CC: Use a fixed small time instead to make it possible to stop
            #          the thread in time. Use a timer interval for `update_secs`
            time.sleep(update_secs)

            stop_flag = threads[username][1].load()
            if stop_flag == 1:
                break

            ctx.bot.send_message(
                chat_id=owner.id,
                text=json.dumps(
                    nation,
                    indent=4
                )
            )

            upd.message.reply_text()

    thread = threading.Thread(target=monitor)
    stop_flag = atomics.atomic(width=4, atype=atomics.INT)
    stop_flag.store(0)
    threads[username] = (thread, stop_flag)
    upd.message.reply_text(
        f'Monitoring {nation_code}'
    )
    thread.start()

monitor_armies.threads = {}

def show_help(upd, ctx):
    upd.message.reply_text(
        '/help: Show this message\n'
        '/ng: Play a round of *Nation Game*\n'
        '/map: Show the world map [WIP]\n'
        '/dep NATION_CODE SOLDIERS_AMOUNT [ENEMIES]: Deploy soldiers\n'
        '/att NATION_CODE [ENEMIES]: Start offernsive\n'
        '/nati NATION_CODE: Get info on nation\n'
        '/mon NATION_CODE TIME: Get sent private nation updates every TIME seconds\n'
        '/mon STOP: Stop private updates\n'
        '/save: Save world map and player data'
    )

round_handler = ConversationHandler(
    entry_points=[
        CommandHandler('help', show_help),
        CommandHandler('ng', start_round),
        CommandHandler('map', show_world_map),
        CommandHandler('save', save_game),
        CommandHandler('dep', deploy_army()),
        CommandHandler('att', begin_offensive),
        CommandHandler('nati', show_nation_info),
        CommandHandler('mon', monitor_armies),

        # Administrator commands for testing
        CommandHandler('adep', deploy_army(admin=True)),
    ],
    states={
        RECV_ANS: [MessageHandler(Filters.text, receive_ans)],
        # HANDLE_WIN: [MessageHandler(Filters.photo, photo)]
        # LOCATION: [
        #     MessageHandler(Filters.location, location),
        #     CommandHandler('skip', skip_location),
        # ],
        # BIO: [MessageHandler(Filters.text & ~Filters.command, bio)],
    },
    fallbacks=[CommandHandler('cancel', cancel_round)],
    per_user=False
)
