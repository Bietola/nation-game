import time
import threading
from utils import eprint

def start_sim_thread(step_fun, world, ticks_in_sec, update_secs, name=None):
    if not name:
        name = step_fun.__name__

    # TODO: Add logging levels
    eprint(f'sim thread: {name}: LOG: START')

    # TODO: Handle offline sim
    def sim():
        while True:
            # TODO: Add logging levels
            time.sleep(update_secs)
            eprint(f'sim thread: {name}: STEP')
            nonlocal world
            world = step_fun(world, update_secs * ticks_in_sec)

    handle = threading.Thread(
        target=sim
    )

    handle.start()

    return handle

# e.g. start_sim_therad(war_sim.step, world, 50 / 24 / 60 / 60)