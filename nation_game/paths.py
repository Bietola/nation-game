from pathlib import Path
from appdirs import *

APP_NAME = 'nation-game'
APP_AUTHOR = 'bietola'

DATA = Path(__file__).parent / 'data'

# CACHE = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
# ASSETS = Path(user_data_dir(APP_NAME, APP_AUTHOR)) / 'assets'
CACHE = DATA / 'cache'
ASSETS = DATA / 'assets'
GAME_DATA = DATA / 'game-data'

LOG = GAME_DATA / 'log.txt'

# TODO: Use metaprogramming?
ALL_PATHS = [CACHE, ASSETS, GAME_DATA, LOG]
