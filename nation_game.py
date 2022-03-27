from telegram.ext import CommandHandler, ConversationHandler, MessageHandler
from telegram.ext.filters import Filters
from numbers import Number
import graphviz
import random
import re
from lenses import lens
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
from threading import Lock
from functools import partial

import emoji_utils as emjutl

# Constants
NG_PHASE_DELTA = 60 * 5
WAR_PHASE_DELTA = 60 * 1
NG_ENABLED_GROUPS = [-1001641644487] # TODO: Make this configurable

# Globals
g_chosen_flag = {}
g_ng_ok = True
g_ng_phase_start_t = time.time()

# Game states
RECV_ANS = range(1)

g_db = {
    'lock': Lock(),
    'players': defaultdict(
        lambda: {'tot_points': 0, 'points': 0},
        json.loads(Path('./assets/players.json').open().read())
    ),
    'world': json.loads(Path('./assets/world.json').open().read())
}

def db(field):
    global g_db
    return g_db[field]

def flush_db(field=None):
    global g_db

    if not field:
        for f in ['world', 'players']:
            flush_db(f)
        return

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

    if upd.effective_chat.id not in NG_ENABLED_GROUPS:
        send_txt(f'smh [ng not allowed in group id {-1001641644487}]')
        return ConversationHandler.END

    global g_ng_phase_start_t
    global g_ng_ok
    now = time.time()
    delta = now - g_ng_phase_start_t
    cur_phase_delta = NG_PHASE_DELTA if g_ng_ok else WAR_PHASE_DELTA
    if delta > cur_phase_delta:
        g_ng_phase_start_t = now
        g_ng_ok = not g_ng_ok

    time_left = round(cur_phase_delta - delta)

    if not g_ng_ok:
        send_txt(f'No ng you fool, go do war [t-{time_left}]')
        return ConversationHandler.END

    send_txt(f'Let the game commence [t-{time_left}]')

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
        db('lock').acquire()
        winner_data = db('players')[user.username]
        tot_points = winner_data['tot_points']
        points = winner_data['points']

        upd.message.reply_text(
            f'{user.name} is the winner [{points + 1}/{tot_points + 1}]'
        )

        # Record win
        winner_data['points'] += 1
        winner_data['tot_points'] += 1

        db('lock').release()

        return ConversationHandler.END

    else:
        upd.message.reply_text(f'{user.name}, you are wrong D:')
        return RECV_ANS

def cancel_round(upd, ctx):
    return ConversationHandler.END

def print_world_map(get_color, title='World Map', max_color_range=25000):
    df = pd.DataFrame.from_dict(
        db('world')
    )

    df['Color'] = df.apply(get_color, axis=1)

    fig = px.choropleth(
        df,
        locations='Country Code',
        color='Color',
        hover_name='Country Name',
        title=title,
        color_continuous_scale='Viridis',
        range_color=(0, max_color_range)
    )

    map_path = Path(__file__).parent / 'assets/cache/world-map.png'
    fig.write_image(map_path)

    return map_path

def show_ranking(upd, ctx):
    upd.message.reply_text(json.dumps(db('players'), indent=4))

def show_world_map(upd, ctx):
    owner = ctx.args[0] if len(ctx.args) > 0 else 'Natives'
    max_color_range = int(ctx.args[1]) if len(ctx.args) > 1 else 25000

    map_path = print_world_map(
        title=f'Armies of {owner}',
        max_color_range=max_color_range,
        get_color=lambda nation: next(filter(
            lambda army: army['Owner'] == owner,
            list(nation['Armies'])
        ), {'Strength': 0})['Strength'],
    )

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

    if nation:
        return Ok(nation)

    nation = filter(
        lambda nat: nat['Country Name'].lower() == nation_code.lower(),
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
                f'Not enough points, deploying all ({players[owner]["points"]})'
            )
            amount = players[owner]['points']

        # NB. This creates an empty army if there isn't one
        army = find_army(world, nation_code, owner)
        if isinstance(army, Err):
            upd.message.reply_text(
                army.value
            )
            return
        army = army.value

        if amount < -army['Strength']:
            upd.message.reply_text(
                f'Not enough soldiers, full retreat (-{army["Strength"]})'
            )
            amount = -army['Strength']

        army['Strength'] += amount
        if not admin or amount < 0:
            players[owner]['points'] -= amount

        res = apply_offensive_opts(owner, nation_code, off_opts)
        if isinstance(res, Err):
            upd.message.reply_text(res.value)

        upd.message.reply_text('Sucessfuly deployed')

    return handler

def apply_offensive_opts(offender, nation_code, opts):
    world = db('world')

    # NB. This creates an empty army if there isn't one
    nation = find_nation(world, nation_code)
    if isinstance(nation, Err):
        return nation
    nation = nation.value
    army = find_army(world, nation_code, offender)
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
            elif opp not in map(
                    lambda army: army['Owner'],
                    nation['Armies']):
                return Err(f'ERR: {opp} not present in {nation["Country Name"]}')
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
            'Usage: nati (NATION_CODE or NATION_NAME)'
        )
        return

    nation_code = ctx.args[0]

    world = db('world')

    res = find_nation(world, nation_code)
    if isinstance(res, Err):
        upd.message.reply_text(res.value)
    nation = res.value

    upd.message.reply_text(json.dumps(
        # lens.Recur(Number).modify(lambda x: round(x, 3))(nation),
        lens.Item('Armies').set(None)(nation),
        indent=4
    ))

    # Print piechart of armies
    df = pd.DataFrame.from_dict(
        nation['Armies']
    )

    fig = px.pie(df, values='Strength', names='Owner', title='Test')
    data_path = Path(__file__).parent / 'assets/cache/nation-info-armies.png'
    fig.write_image(data_path)

    ctx.bot.send_photo(
        chat_id=upd.effective_chat.id,
        photo=data_path.open('rb')
    )

    # Print attack relationships
    dot = graphviz.Digraph(comment='Offensive plans')
    for army in nation['Armies']:
        dot.node(army['Owner'])
        for opp in army['Fighting']:
            dot.edge(army['Owner'], opp)

    data_path = Path(__file__).parent / 'assets/cache/nation-info-att'
    dot.render(data_path, format='png')
    data_path = data_path.parent / (data_path.name + '.png')

    ctx.bot.send_photo(
        chat_id=upd.effective_chat.id,
        photo=data_path.open('rb')
    )

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
        upd.message.reply_text('Stopping monitor...')
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
                ctx.bot.send_message(
                    chat_id=owner.id,
                    text='Monitoring stopped'
                )
                break

            ctx.bot.send_message(
                chat_id=owner.id,
                text=json.dumps(
                    nation,
                    indent=4
                )
            )

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
        '/map <PLAYER> <RESOLUTION>: Show the world map with PLAYER army size\n'
        '/dep NATION_CODE SOLDIERS_AMOUNT [ENEMIES]: Deploy soldiers\n'
        '/att NATION_CODE [ENEMIES]: Start offernsive\n'
        '/nati NATION_CODE: Get info on nation\n'
        '/mon NATION_CODE TIME: Get sent private nation updates every TIME seconds\n'
        '/mon STOP: Stop private updates\n'
        '/save: Save world map and player data'
    )

def lock_db(fun, *args):
    global g_db
    db('lock').acquire()

    fun(*args)

    db('lock').release()

round_handler = ConversationHandler(
    entry_points=[
        CommandHandler('help', show_help),
        CommandHandler('ng', start_round),
        CommandHandler('rank', show_ranking),
        CommandHandler('map', show_world_map),
        CommandHandler('save', partial(lock_db, save_game)),
        CommandHandler('dep', partial(lock_db, deploy_army())),
        CommandHandler('att', partial(lock_db, begin_offensive)),
        CommandHandler('nati', show_nation_info),
        CommandHandler('mon', monitor_armies),

        # Administrator commands for testing
        CommandHandler('adep', partial(lock_db, deploy_army(admin=True))),
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
