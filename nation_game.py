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


import emoji_utils as emjutl

g_chosen_flag = {}

# Game states
RECV_ANS = range(1)


g_db = {}
g_db['players'] = defaultdict(
    lambda: {'points': 0},
    json.loads(Path('./assets/players.json').open().read())
)
g_db['world'] = json.loads(Path('./assets/world.json').open().read())


def db(field):
    global g_db
    return g_db[field]


def flush_db(field):
    global g_db
    Path(f'./assets/{field}.json').write_text(
        json.dumps(g_db[field]),
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
        upd.message.reply_text(db('players'))
        return RECV_ANS

    elif upd.message.text.lower() == 'cheat':
        upd.message.reply_text(f'answer: {g_chosen_flag["name"]}')
        return RECV_ANS

    elif upd.message.text.lower() == 'cancel':
        upd.message.reply_text(f'No more (answer: {g_chosen_flag["name"]})')
        return ConversationHandler.END

    elif upd.message.text.lower() == extract_flag_name(g_chosen_flag['name']).lower():
        winner_data = db('players')[user.username]

        upd.message.reply_text(
            f'{user.name} is the winner [points: {winner_data["points"] + 1}]')

        # Record win
        winner_data['points'] += 1
        flush_db('palyers')

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

round_handler = ConversationHandler(
    entry_points=[
        CommandHandler('ng', start_round),
        CommandHandler('map', show_world_map)
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
