from pathlib import Path
import emoji
import json
import random

# Return database of emojis as dictionary (kept as static function variable)
def db():
    if db.db == None:
        db.db = json.loads(Path('./assets/emojis.json').open().read())['emojis']
        print('Loaded giant emoji json')
    return db.db
db.db = None
