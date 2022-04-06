import fire
from telegram.ext import Updater
from telegram.ext import CommandHandler
from pathlib import Path
import time
import os

import nation_game.utils as utils
import nation_game.register as register
import nation_game.bot as bot
from nation_game.register import RegChats
import nation_game.sim_thread as sim_thread
import nation_game.paths as paths

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
    dispatcher.add_handler(bot.round_handler)

    ###################
    # Start Things Up #
    ###################

    game = bot.g_db

    ticks_in_sec = game['sim-speed'] * (50 / 24 / 3600) # 50 ticks = 1 day; sim-speed-x speedup

    # Start world simulation
    # TODO: Make sim thread terminations graceful useing the handle
    import nation_game.war_sim as war_sim
    _war_sim_h = sim_thread.start_sim_thread(
        name='War',
        step_fun=war_sim.step,
        game=game, # TODO: This is shit
        ticks_in_sec=ticks_in_sec,
        # update_secs=100,
        update_secs=10 # for DB
    )

    # NB. Not really a simulation... just saves the game state to disk
    import nation_game.save_game_sys as save_game_sys
    _save_sim_h = sim_thread.start_sim_thread(
        name='Save Game',
        step_fun=save_game_sys.step,
        game=bot.g_db, # TODO: This is shit
        ticks_in_sec=1, # Not needed...
        update_secs=60 # Save every 1min
    )

    # NB. Not really a simulation... just saves the game state to disk
    import nation_game.sim_occupation_production as sim_occupation_production
    _occ_b_sim_h = sim_thread.start_sim_thread(
        name='Occ B.',
        step_fun=sim_occupation_production.step,
        game=bot.g_db, # TODO: This is shit
        ticks_in_sec=ticks_in_sec,
        update_secs=10
    )

    # Create needed game folders / files
    for path in paths.ALL_PATHS:
        if not os.path.exists(path):
            if path.is_file():
                with open(path, 'w'):
                    pass
            else:
                path.mkdir(parents=True)

    # Start bot
    updater.start_polling()

###############
# Entry Point #
###############

def cli():
    fire.Fire(nation_game_bot)

if __name__ == '__main__':
    cli()
