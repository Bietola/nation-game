from pathlib import Path

from utils import SRC_PATH

# TODO: Find out why duplicates exist
class RegChats:
    val = None

    def parse_regchats():
        with open(SRC_PATH / Path('registered_chats'), 'r') as f:
            content = f.readlines()

        return set([ ln.strip() for ln in content ])

    def init():
        if RegChats.val == None:
            RegChats.val = RegChats.parse_regchats()

    def get():
        RegChats.init()
        return RegChats.val

    def add(chat_id):
        RegChats.init()
        RegChats.val.add(chat_id)

def handler(upd, ctx):
    RegChats.add(upd.effective_chat.id)
    ctx.bot.send_message(
        chat_id = upd.effective_chat.id,
        text = 'Chat registered'
    )

def commit(upd, ctx):
    regchats_path = SRC_PATH / Path('registered_chats')

    regchats_path.unlink()

    with open(regchats_path, 'w') as f:
        for i in RegChats.val:
            print(i, file=f)
