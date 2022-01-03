import fire
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from functools import *
from pathlib import Path
import random
import os
import threading
import time
import inspect
import emoji
import json

import utils
from utils import eprint, shell, SRC_PATH

import register
import nation_game
from register import RegChats

####################
# Global Variables #
####################

# None for now

##################################
# Helper Functions ans Constants #
##################################

def cur_time():
    return time.strftime("%H:%M:%S", time.localtime())

########
# Main #
########

def nation_game_bot(max_spam_lv=1):
    # Basic logging functions
    def log(txt, silent=False, notify=True, spam_lv=1):
        print(f'main_thread: {txt}')

        if spam_lv <= max_spam_lv and not silent:
            regchats = RegChats.get()

            for chat_id in RegChats.get():
                updater.bot.send_message(
                    chat_id = chat_id,
                    text = txt,
                    disable_notification = not notify
                )

    ################################
    # Get access to bot with token #
    ################################

    utils.wait_until_connected(delay=20, trace=True)
    updater = Updater(
        token=(Path(__file__).parent.resolve() / 'token').read_text().strip(),
        use_context=True
    )
    dispatcher = updater.dispatcher


    #############
    # Bot Intro #
    #############

    # log('NationGameBot is awake')

    ############
    # Handlers #
    ############

    dispatcher.add_handler(
        CommandHandler(
            'register',
            register.handler
        )
    )

    dispatcher.add_handler(
        CommandHandler(
            'regcommit',
            register.commit
        )
    )

    dispatcher.add_handler(
        CommandHandler(
            'insult',
            lambda upd, ctx: ctx.bot.send_message(
                chat_id = upd.effective_chat.id,
                text = "no u"
            )
        )
    )

    # TODO: Also add query handler
    log(f'Nation game handler active (time: {cur_time()})', spam_lv=2)
    dispatcher.add_handler(nation_game.round_handler)

    ###################
    # Start Things Up #
    ###################

    # # Minecraft server check
    # threading.Thread(
    #     target = minecraft.server_inactivity_checker(updater.bot)
    # ).start()

    # Start bot
    updater.start_polling()

###############
# Entry Point #
###############

if __name__ == '__main__':
    fire.Fire(nation_game_bot)