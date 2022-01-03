from telegram import Update, Message, Chat, MessageEntity
from telegram.ext import Updater
from telegram.ext import CommandHandler 
import sys

import conf
# from main import updater
from utils import eprint

################################
# Get access to bot with token #
################################

# updater = Updater(token='1516509922:AAHd36t-69qu1FolhavdCo6_qb_UJnFPix4', use_context=True)

# updater.bot.send_message(
#     chat_id = conf.get('admin_chat_id'),
#     text = '/insult'
# )

updater.dispatcher.process_update(
    Update(
        update_id = 0,
        message = Message(
            message_id = 0,
            date = datetime.now(),
            chat = Chat(
                id = conf.get('admin_chat_id'),
                type = '???'
            ),
            entities = [
                MessageEntity(
                )
            ]
        )
    )
)
