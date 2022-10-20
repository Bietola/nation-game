from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler
import telegram.ext.filters as filters
from numbers import Number
import operator as op
import graphviz
import random
import math
import re
from file_read_backwards import FileReadBackwards
from lenses import lens, bind
from collections import defaultdict
import json
import pickle
import pandas as pd
import plotly.express as px
from pathlib import Path
from result import Result, Ok, Err
import datetime
import time
import atomics
import threading
from threading import Lock
from itertools import islice
from functools import partial

import nation_game.utils as utils
from nation_game.utils import awaitify
import nation_game.emoji_utils as emjutl
from nation_game.world import *
import nation_game.paths as paths

# Constants
NG_PHASE_DELTA = 60 * 5
WAR_PHASE_DELTA = 30 * 1
NG_ENABLED_GROUPS = [-1001641644487] # TODO: Make this configurable

# To be enums
ALL_SCOPES = ['world', 'usa', 'europe', 'asia', 'africa', 'north_america', 'south_america']
UNIT_TYPES = ['military', 'factories']
SPECIAL_UNIT_TYPES = ['factories']

# Globals
g_chosen_flag = {}
g_ng_ok = True
g_ng_phase_start_t = time.time()

# Game states
RECV_ANS = range(1)

def _log(contents):
    log_file = paths.LOG
    log_path = log_file.resolve()

    with FileReadBackwards(log_path, encoding='utf-8') as logf:
        last_line = logf.readline()

    if m := re.compile(r'^(\d+?):').match(last_line):
        line_n = (int(m.group(1)) + 1) % 100
    else:
        line_n = 0

    contents = f'{line_n}: {contents}'
    print(contents)
    print(contents, file=log_file.open('a'))

g_db = {
    'players': defaultdict(
        lambda: {
            'active': False,
            'tot_points': 0,
            'points': 0,
            'production': 0,
            'solo_energy': 100,
            'battle_energy': 100,
        },
        pickle.loads(
            (paths.GAME_DATA / 'players.pickle').read_bytes()
        )
    ),

    'world': pickle.loads(
        (paths.GAME_DATA / 'world.pickle').read_bytes()
    ),

    'lock': Lock(),
    'sim-speed': 20,
    'energy-recharge': {
        'solo': 100,   # energy/day
        'battle': 100, # energy/day
    },

    'log': _log,

    # # TODO: Put in seperate file (including default values)
    # 'unit-types': defaultdict(
    #     lambda: {
    #         # ...
    #     },
    #     [
    #         'military': {
    #             build_occ_req: 0.0,
    #             can_attack: True
    #         },
    #         'factories': {
    #             ind_bonus: ''
    #             build_occ_req: 0.7,
    #             can_attack: False
    #         }
    #     ]
    # )

}

def db_set(field, lens1, lock=False):
    global g_db
    if lock: db('lock').acquire()
    g_db[field] = lens1(g_db[field])
    if lock: db('lock').release()

def db(field):
    global g_db
    return g_db[field]

def flush_db(field=None):
    global g_db

    if not field:
        for f in ['world', 'players']:
            flush_db(f)
        return

    if isinstance(g_db[field], defaultdict):
        to_pickle = dict(g_db[field])
    else:
        to_pickle = g_db[field]
    (paths.GAME_DATA / f'{field}.pickle').write_bytes(
        pickle.dumps(to_pickle)
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
async def start_round(upd, ctx):
    async def send_txt(txt):
        await ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=txt
        )

    if upd.effective_chat.id not in NG_ENABLED_GROUPS:
        await send_txt(f'smh [ng not allowed in group id {upd.effective_chat.id}]')
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
        await send_txt(f'No ng you fool, go do war [t-{time_left}]')
        return ConversationHandler.END

    await send_txt(f'Let the game commence [t-{time_left}]')

    round_starter = upd.message.from_user.username 
    db_set('players', lens[round_starter]['active'].set(True), lock=True)

    global g_chosen_flag
    g_chosen_flag = random.choice(
        list(filter(lambda e: 'flag' in e['name'], emjutl.db())))
    await send_txt(g_chosen_flag['emoji'])

    return RECV_ANS

def cancel_round(upd, ctx):
    return ConversationHandler.END

async def receive_ans(upd, ctx):
    user = upd.message.from_user

    db_set('players', lens[user.username]['active'].set(True), lock=True)

#    if db('players')[user.username]['battle_energy'] <= 0:
#        upd.message.reply_text(f'Battle energy over (wait for next recharge)')
#        return RECV_ANS

    if upd.message.text.lower() == 'ranking':
        await upd.message.reply_text(json.dumps(db('players'), indent=4))
        return RECV_ANS

    elif upd.message.text.lower() == 'cheat':
        await upd.message.reply_text(f'answer: {g_chosen_flag["name"]}')
        return RECV_ANS

    elif upd.message.text.lower() == 'cancel':
        await upd.message.reply_text(f'No more (answer: {g_chosen_flag["name"]})')
        db_set('players', lens.Values()['active'].set(False))
        return ConversationHandler.END

    elif upd.message.text.lower() == extract_flag_name(g_chosen_flag['name']).lower():
        db('lock').acquire()

        pls = db('players')
        
        prize = sum(
            bind(pls).Values()['active']
                .F(int)
                .collect()
        )

        db_set('players', lens.Values()['active'].set(False))

        # Record win
        winner = db('players')[user.username]
        winner['points'] += prize
        winner['tot_points'] += prize

        await upd.message.reply_text(
            f'{user.name} is the winner (+{prize}) [{round(winner["points"], 4)}/{winner["tot_points"]}]'
        )

        db('lock').release()

        return ConversationHandler.END

    else:
        await upd.message.reply_text(f'{user.name}, you are wrong D:')
        return RECV_ANS

async def dump_log(upd, ctx, ret=True):
    pattern = ctx.args[0] if len(ctx.args) >= 1 else '.*'
    lines_back = int(ctx.args[1]) if len(ctx.args) >= 2 else 5

    pattern = re.compile(pattern)
    with FileReadBackwards(
        paths.LOG,
        encoding='utf-8'
    ) as logf:
        lines = list(islice(filter(
            lambda l: pattern.search(l),
            logf
        ), lines_back))
        lines.reverse()

        await upd.message.reply_text(
            '\n'.join(lines) if len(lines) != 0 else 'No messages?'
        )

    if ret:
        return ConversationHandler.END

async def list_occupied_nations(upd, ctx):
    global g_db

    if len(ctx.args) > 1:
        await upd.message.reply_text(
            'Usage: `/lsoc <PLAYER>'
        )
        return ConversationHandler.END

    owner = ctx.args[0] if len(ctx.args) > 0 else upd.message.from_user.username

    def perc(nation, army):
        return round(100 * army['Strength'] / sum(lens.Each()['Strength'].collect()(nation['Armies'])), 2)

    reply = []
    for nation in db('world'):
        for army in nation['Armies']:
            if army['Owner'] == owner:
                world = db('world')
                occ_perc = int(
                    nation_occupation_perc(world, nation["Country Code"], army["Owner"]).value * 100
                )
                reply.append(
                    f'{nation["Country Name"]}: {round(army["Strength"], 2)} ({occ_perc})'
                )

    if len(reply) == 0:
        await upd.message.reply_text('No armies?')
    else:
        await upd.message.reply_text('\n'.join(reply))

async def show_speed(upd, ctx):
    await upd.message.reply_text(
        f'{db("sim-speed")}x'
    )
    return ConversationHandler.END

async def show_map_scopes(upd, ctx):
    await upd.message.reply_text(f'{ALL_SCOPES}')
    return ConversationHandler.END

async def show_todo(upd, ctx):
    todo_file = ctx.args[0] if len(ctx.args) > 0 else 'main'

    if todo_file == 'list':
        await upd.message.reply_text(
            list(map(lambda p: p.name, (paths.ASSETS / 'todo').rglob('*')))
        )
        return ConversationHandler.END

    await upd.message.reply_text(
        (paths.ASSETS / f'todo/{todo_file}.md')
        .open(encoding='utf8').read()
    )
    return ConversationHandler.END

def print_world_map(get_color, title='World Map', scope='world', max_color_range=25000):
    scope = scope.replace('_', ' ')

    df = pd.DataFrame.from_dict(
        db('world')
    )

    df['Color'] = df.apply(get_color, axis=1)

    fig = px.choropleth(
        df,
        locations='Country Code',
        color='Color',
        hover_name='Country Name',
        scope=scope,
        title=title,
        color_continuous_scale='Viridis',
        range_color=(0, max_color_range)
    )

    map_path = paths.CACHE / 'world-map.png'
    fig.write_image(map_path)

    return map_path

async def show_ranking(upd, ctx):
    await upd.message.reply_text(
        json.dumps(
            lens.Recur(Number).modify(lambda x: round(x, 3))(db('players')),
            indent=4
        )
    )

    return ConversationHandler.END

async def show_world_map(upd, ctx):
    owner = ctx.args[0] if len(ctx.args) > 0 else 'Natives'
    scope = ctx.args[1] if len(ctx.args) > 1 else 'world'
    max_color_range = int(ctx.args[2]) if len(ctx.args) > 2 else 25000

    # "map all ...": divide map in dominions using player colors
    if owner == 'all':
        get_color

    map_path = print_world_map(
        title=f'Armies of {owner}',
        scope=scope,
        max_color_range=max_color_range,
        get_color=lambda nation: next(filter(
            lambda army: army['Owner'] == owner,
            list(nation['Armies'])
        ), {'Strength': 0})['Strength'],
    )

    await ctx.bot.send_photo(
        chat_id=upd.effective_chat.id,
        photo=map_path.open('rb')
    )

async def save_game(upd, ctx):
    flush_db('players')
    await ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text='Player data saved'
    )

    flush_db('world')
    await ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text='World map saved'
    )

def deploy_units(admin=False, unit_type='Military'):
    async def handler(upd, ctx):
        if len(ctx.args) < 2:
            await upd.message.reply_text(
                'Usage: `/dep NATION_CODE AMOUNT TYPE? (+/-)OPPONENTS*'
            )
            return

        nation_code = ctx.args[0]
        amount = int(ctx.args[1])
        unit_type = ctx.args[2] if len(ctx.args) >= 3 else 'Military'
        off_opts = ctx.args[3:]

        deploy_from = upd.message.from_user.username

        valid_unit_types = list(utils.all_prefix_matches(
            unit_type.lower(),
            UNIT_TYPES
        ))
        if len(valid_unit_types) == 0:
            await upd.message.reply_text(
                'ERR: Malformed unit type.'
            )
            return ConversationHandler.END
        elif len(valid_unit_types) > 1:
            await upd.message.reply_text(
                'ERR: Ambiguous unit type.\n'
                '\n'.join(valid_unit_types)
            )
            return ConversationHandler.END
        else:
            unit_type = valid_unit_types[0]

        if unit_type == 'military':
            deploy_to = upd.message.from_user.username
        else:
            # Factories
            deploy_to = 'factories'

        if deploy_to in SPECIAL_UNIT_TYPES: deploy_to = '_' + deploy_to

        world = db('world')
        players = db('players')

        if not admin and amount > players[deploy_from]['points']:
            await upd.message.reply_text(
                f'Not enough points, deploying all ({players[deploy_from]["points"]})'
            )
            amount = players[deploy_from]['points']

        # NB. This creates an empty army if there isn't one
        nation = find_nation(world, nation_code)
        if isinstance(nation, Err):
            await upd.message.reply_text(
                nation.value
            )
            return
        nation = nation.value

        if deploy_to == '_factories':
            factories = next(filter(
                lambda a: a['Owner'] == '_factories',
                nation['Armies']
            ), {'Strength': 0})['Strength']
            if amount + factories > nation['Price']:
                await upd.message.reply_text(
                    f'Too many {deploy_to} units! Building max ({nation["Price"]}).'
                )
                amount = nation['Price']
            if amount < 0:
                await upd.message.reply_text(
                    f'ERR: Can\'t {deploy_to} units not removable.'
                )
                return ConversationHandler.END
            if nation_occupation_perc(world, nation_code, deploy_from).value < 0.7:
                await upd.message.reply_text(
                    f'ERR: Can\'t deploy {deploy_to} units, occupation needed.'
                )
                return ConversationHandler.END

        # NB. This creates an empty army if there isn't one
        army = find_army(world, nation_code, deploy_to)
        if isinstance(army, Err):
            await upd.message.reply_text(
                army.value
            )
            return
        army = army.value

        if amount < -army['Strength']:
            await upd.message.reply_text(
                f'Not enough soldiers, full retreat (-{army["Strength"]})'
            )
            amount = -army['Strength']

        army['Strength'] += amount
        if not admin or amount < 0:
            players[deploy_from]['points'] -= amount

        res = apply_offensive_opts(deploy_from, nation_code, off_opts)
        if isinstance(res, Err):
            await upd.message.reply_text(res.value)

        await upd.message.reply_text('Sucessfuly deployed')

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

async def show_nation_info_raw(upd, ctx):
    if len(ctx.args) != 1:
        await upd.message.reply_text(
            'Usage: raw (NATION_CODE or NATION_NAME)'
        )
        return

    nation_code = ctx.args[0]

    world = db('world')

    res = find_nation(world, nation_code)
    if isinstance(res, Err):
        await upd.message.reply_text(res.value)
    nation = res.value

    await upd.message.reply_text(json.dumps(
        lens.Recur(Number).modify(lambda x: round(x, 3))(nation),
        indent=4
    ))

async def show_nation_info(upd, ctx):
    if len(ctx.args) != 1:
        await upd.message.reply_text(
            'Usage: nati (NATION_CODE or NATION_NAME)'
        )
        return

    nation_code = ctx.args[0]

    world = db('world')

    res = find_nation(world, nation_code)
    if isinstance(res, Err):
        await upd.message.reply_text(res.value)
    nation = res.value

    await upd.message.reply_text(json.dumps(
        # lens.Recur(Number).modify(lambda x: round(x, 3))(nation),
        lens.Item('Armies').set(None)(nation),
        indent=4
    ))

    # Print piechart of armies
    df = pd.DataFrame.from_dict(
        filter(
            # 1: removes the leading `_`
            lambda a: a['Owner'][1:] not in SPECIAL_UNIT_TYPES,
            nation['Armies']
        )
    )

    fig = px.pie(df, values='Strength', names='Owner', title='Test')
    data_path = paths.CACHE / 'nation-info-armies.png'
    fig.write_image(data_path)

    await ctx.bot.send_photo(
        chat_id=upd.effective_chat.id,
        photo=data_path.open('rb')
    )

    # Print attack relationships
    dot = graphviz.Digraph(comment='Offensive plans')
    for army in nation['Armies']:
        dot.node(army['Owner'], f'{army["Owner"]} ({math.floor(army["Strength"])})')
        for opp in army['Fighting']:
            dot.edge(army['Owner'], opp)

    data_path = paths.CACHE / 'nation-info-att'
    dot.render(data_path, format='png')
    data_path = data_path.parent / (data_path.name + '.png')

    await ctx.bot.send_photo(
        chat_id=upd.effective_chat.id,
        photo=data_path.open('rb')
    )

def gift_points(upd, ctx):
    rx = ctx.args[0]
    amount = int(ctx.args[1])

    g_db['players'][rx]['points'] += amount

    upd.message.reply_text('Points gifted')

    return ConversationHandler.END

def monitor_armies(upd, ctx):
    if len(ctx.args) < 1:
        upd.message.reply_text(
            'Usage: mon (-t UPDATE_SECS=10) (log LOG_ARGS*)|stop|NATION_CODE'
        )
        return

    if ctx.args[0] == '-t':
        update_secs = ctx.args[1]
        ctx.args = ctx.args[2:]
    else:
        update_secs = 10

    nation_code = ctx.args[0]
    log_args = ctx.args[1:] if len(ctx.args) >= 1 else None

    owner = upd.message.from_user
    username = owner.username
    threads = monitor_armies.threads

    if nation_code == 'stop':
        upd.message.reply_text('Stopping monitor...')
        threads[username][1].store(1)
        threads[username][0].join()
        threads.pop(username)
        return

    world = db('world')

    if nation_code != 'log':
        res = find_nation(world, nation_code)
        if isinstance(res, Err):
            upd.message.reply_text(res.value)
            return ConversationHandler.END
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

            if nation_code == 'log':
                ctx.args = log_args
                dump_log(upd, ctx, ret=False)
            else:
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

    return ConversationHandler.END

monitor_armies.threads = {}

async def show_help(upd, ctx):
    await upd.message.reply_text(
        '/help: Show this message\n'
        '/ng: Play a round of *Nation Game*\n'
        '/map <PLAYER> <RESOLUTION>: Show the world map with PLAYER army size\n'
        '/dep NATION_CODE SOLDIERS_AMOUNT [ENEMIES]: Deploy soldiers\n'
        '/att NATION_CODE [ENEMIES]: Start offernsive\n'
        '/nati NATION_CODE: Get info on nation\n'
        '/raw NATION_CODE: Get raw json info on nation\n'
        '/mon NATION_CODE TIME: Get sent private nation updates every TIME seconds\n'
        '/mon stop: Stop private updates\n'
        '/lsoc <PLAYER>: Show all armies of PLAYER (or yours)\n'
        '/save: Save world map and player data\n'
        '/todo: Show todo list of game changes\n'
        '/todo list: List todo files\n'
        '/todo FILE_NAME: Show todo list named FILE_NAME\n'
        '/speed: Show simulation speed\n'
    )

def lock_db(fun):
    async def ret(*args):
        global g_db
        db('lock').acquire()

        await fun(*args)

        db('lock').release()
    return ret

async def test_button_launch(upd, ctx) -> None:
    """Sends a message with three inline buttons attached."""
    # TODO/CC: Use command hints and sub-conversations instead of keyboard
    keyboard = [
        [
            KeyboardButton("Deploy soldiers", callback_data="1"),
            KeyboardButton("Define offensive", callback_data="2"),
            KeyboardButton("Show map", callback_data="3"),
        ],
        [
            KeyboardButton("Show occupied territories", callback_data="4"),
            KeyboardButton("Show log", callback_data="5")
        ],
        [
            KeyboardButton("Build factories", callback_data="6"),
        ]
    ]

    await upd.message.reply_text(
        "Please choose:",
        reply_markup=ReplyKeyboardRemove()
        # reply_markup=ReplyKeyboardMarkup(
        #     keyboard,
        #     one_time_keyboard=True
        # )
    )

    return ConversationHandler.END

async def test_button(upd, ctx) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = upd.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")


round_handler = ConversationHandler(
    entry_points=[
        CommandHandler('test', test_button_launch),
        CommandHandler('help', show_help),
        CommandHandler('ng', start_round),
        CommandHandler('rank', show_ranking),
        CommandHandler('map', show_world_map),
        CommandHandler('save', lock_db(save_game)),
        CommandHandler('dep', lock_db(deploy_units())),
        CommandHandler('att', lock_db(begin_offensive)),
        CommandHandler('nati', show_nation_info),
        CommandHandler('raw', show_nation_info_raw),

        # TODO: Convert these into PTB v20 with async
        CommandHandler('mon', monitor_armies),

        CommandHandler('lsoc', list_occupied_nations),
        CommandHandler('todo', show_todo),
        CommandHandler('speed', show_speed),
        CommandHandler('dump', dump_log),
        CommandHandler('scopes', show_map_scopes)

        # Administrator commands used to be here. f
    ],
    states={
        RECV_ANS: [MessageHandler(filters.TEXT, receive_ans)],
        # HANDLE_WIN: [MessageHandler(filters.PHOTO, photo)]
        # LOCATION: [
        #     MessageHandler(filters.LOCATION, location),
        #     CommandHandler('skip', skip_location),
        # ],
        # BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
    },
    fallbacks=[CommandHandler('cancel', cancel_round)],
    per_user=False,
)

callback_query_handler = CallbackQueryHandler(test_button)
