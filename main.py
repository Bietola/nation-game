import fire
from telegram.ext import Updater
from telegram.ext import CommandHandler
from functools import *
from pathlib import Path
import time

import utils

import register
import nation_game
from register import RegChats
import sim_thread

import war_sim

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

    # Main handler used to interact with the game
    log(f'Nation game handler active (time: {cur_time()})', spam_lv=2)
    dispatcher.add_handler(nation_game.round_handler)

    ###################
    # Start Things Up #
    ###################

    # Start world simulation
    # TODO: Make sim thread terminations graceful useing the handle
    # TODO: Add other systems?
    _war_sim_h = sim_thread.start_sim_thread(
        name='War',
        step_fun=war_sim.step,
        world=nation_game.g_db['world'], # TODO: This is shit
        ticks_in_sec=10 * (50 / 24 / 3600), # 50 ticks = 1 day; 10x speedup
        # update_secs=100,
        update_secs=10 # for DB
    )

    # Start bot
    updater.start_polling()

###############
# Entry Point #
###############

if __name__ == '__main__':
    fire.Fire(nation_game_bot)
