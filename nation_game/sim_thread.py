import time
import threading
from utils import eprint

def start_sim_thread(step_fun, game, ticks_in_sec, update_secs, name=None):
    if not name:
        name = step_fun.__name__

    # TODO: Add logging levels
    eprint(f'sim thread: {name}: LOG: START')

    # Because accessing a dict can create a race condition
    game_lock = game['lock']

    # TODO: Handle offline sim
    def sim():
        while True:
            # TODO: Add logging levels
            time.sleep(update_secs)

            nonlocal game
            nonlocal game_lock
            game_lock.acquire()

            eprint(f'sim thread: {name}: STEP')
            game = step_fun(game, update_secs * ticks_in_sec)

            game_lock.release()

    handle = threading.Thread(
        target=sim
    )

    handle.start()

    return handle

# e.g. start_sim_therad(war_sim.step, game, 50 / 24 / 60 / 60)
