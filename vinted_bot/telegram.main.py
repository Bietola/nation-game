#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from pathlib import Path
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import selenium_cmds as scmd

# GLOBAL VARIABLES
g_browser = None

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# GENDER, PHOTO, LOCATION, BIO = range(4)
SEARCH_QUERY = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # """Starts the conversation and asks the user about their gender."""
    # reply_keyboard = [["Search", "Girl", "Other"]]

    # await update.message.reply_text(
    #     'Welcome to VintedBot'
    #     'Send /cancel to stop talking to me.\n\n'
    #     'Enter your search query'
    #     reply_markup=ReplyKeyboardMarkup(
    #         reply_keyboard, one_time_keyboard=True, input_field_placeholder="Boy or Girl?"
    #     ),
    # )

    await update.message.reply_text(
        'Welcome to VintedBot\n'
        'Send /cancel to stop talking to me.\n\n'
        'Enter your search query'
    )

    return SEARCH_QUERY


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    user = update.message.from_user
    logger.info("Gender of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "I see! Please send me a photo of yourself, "
        "so I know what you look like, or send /skip if you don't want to.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return PHOTO


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for a location."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive("user_photo.jpg")
    logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")
    await update.message.reply_text(
        "Gorgeous! Now, send me your location please, or send /skip if you don't want to."
    )

    return LOCATION


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a location."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    await update.message.reply_text(
        "I bet you look great! Now, send me your location please, or send /skip."
    )

    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the location and asks for some info about the user."""
    user = update.message.from_user
    user_location = update.message.location
    logger.info(
        "Location of %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude
    )
    await update.message.reply_text(
        "Maybe I can visit you sometime! At last, tell me something about yourself."
    )

    return BIO


async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the location and asks for info about the user."""
    user = update.message.from_user
    logger.info("User %s did not send a location.", user.first_name)
    await update.message.reply_text(
        "You seem a bit paranoid! At last, tell me something about yourself."
    )

    return BIO


async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # """Stores the info about the user and ends the conversation."""
    # user = update.message.from_user
    # logger.info("Bio of %s: %s", user.first_name, update.message.text)
    # await update.message.reply_text("Thank you! I hope we can talk again some day.")

    global g_browser

    user = update.message.from_user
    query = update.message.text
    logger.info(f'{user.first_name} entered search query: {query}')
    sellers, products = scmd.search_products(g_browser, query, logger)
    first_5 = '\n'.join(products[:5])
    reply_txt = f'Here are the first five products:\n{first_5}'
    await update.message.reply_text(reply_txt)

    # return ConversationHandler.END
    return SEARCH_QUERY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    # Initialize the Selenium browser
    global g_browser
    g_browser = scmd.init_browser(logger)

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(
        Path('./token').read_text('utf8')
    ).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # GENDER: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), gender)],
            # PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler("skip", skip_photo)],
            # LOCATION: [
            #     MessageHandler(filters.LOCATION, location),
            #     CommandHandler("skip", skip_location),
            # ],
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()