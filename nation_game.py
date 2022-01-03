from telegram.ext import CommandHandler, ConversationHandler, MessageHandler
from telegram.ext.filters import Filters
import random
import re
from pathlib import Path
from collections import defaultdict
import json

import emoji_utils as emjutl

g_chosen_flag = {}

# Game states
RECV_ANS = range(1)


g_db = defaultdict(
    lambda: {'points': 0},
    json.loads(Path('./assets/nation-game.json').open().read())
)


def db():
    global g_db
    return g_db


def flush_db():
    global g_db
    Path('./assets/nation-game.json').write_text(
        json.dumps(g_db),
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
        upd.message.reply_text(db())
        return RECV_ANS

    elif upd.message.text.lower() == 'cheat':
        upd.message.reply_text(f'answer: {g_chosen_flag["name"]}')
        return RECV_ANS

    elif upd.message.text.lower() == 'cancel':
        upd.message.reply_text(f'No more (answer: {g_chosen_flag["name"]})')
        return ConversationHandler.END

    elif upd.message.text.lower() == extract_flag_name(g_chosen_flag['name']).lower():
        winner_data = db()[user.username]

        upd.message.reply_text(
            f'{user.name} is the winner [points: {winner_data["points"] + 1}]')

        # Record win
        winner_data['points'] += 1
        flush_db()

        return ConversationHandler.END

    else:
        upd.message.reply_text(f'{user.name}, you are wrong D:')
        return RECV_ANS


def cancel_round(upd, ctx):
    return ConversationHandler.END


round_handler = ConversationHandler(
    entry_points=[CommandHandler('ng', start_round)],
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
