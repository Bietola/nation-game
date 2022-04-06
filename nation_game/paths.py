from pathlib import Path
from appdirs import *

APP_NAME = 'nation-game'
APP_AUTHOR = 'bietola'

CACHE = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
ASSETS = Path(user_data_dir(APP_NAME, APP_AUTHOR)) / 'assets'
GAME_DATA = ASSETS / 'game-data'

LOG = ASSETS / 'log.txt'

# TODO: Use metaprogramming?
ALL_PATHS = [CACHE, ASSETS, GAME_DATA, LOG]
