# pylint: disable=unused-argument


from pathlib import Path
import logging
import wget
import uuid

from pyimagine import Arta
from pyimagine.constants import Style

from transformers import pipeline

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
import MiniCPM_Llama3_V_2_5_selenium as minicpm


# GLOBAL VARIABLES
logger = None
g_browser = None
g_minicpm_ses = None
g_captioner = None
g_cur_list = None
g_cursor = None


# States
TOP_COMMANDS, SEARCH_QUERY, TEST_SEARCH_QUERY = range(3)


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
        'Type /cancel to stop talking to me.\n\n'
        'Type /help for a list of available commands\n'
    )

    return TOP_COMMANDS


async def test_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_browser

    user = update.message.from_user
    query = update.message.text
    logger.info(f'{user.first_name} entered search query: {query}')
    sellers, products = scmd.search_products_soup(g_browser, query, logger)
    # sellers, products = scmd.search_products_soup(query, logger)
    first_5 = '\n'.join(products[:5])
    reply_txt = f'Here are the first five products:\n{first_5}'
    await update.message.reply_text(reply_txt)

    # return ConversationHandler.END
    return TOP_COMMANDS


async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_browser, g_cur_list, g_cursor

    user = update.message.from_user
    query = update.message.text
    logger.info(f'{user.first_name} entered search query: {query}')
    await update.message.reply_text('Performing query...')
    sellers, products = scmd.search_products(g_browser, query, logger)
    # sellers, products = scmd.search_products_soup(query, logger)
    # TODO: For now, taking only the first 10.
    g_cur_list = [{'link': x} for x in products[:10]]
    g_cursor = 0
    reply_txt = f'Found {len(g_cur_list)} products.'
    await update.message.reply_text(reply_txt)

    # return ConversationHandler.END
    return TOP_COMMANDS


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    # Enable logging
    print('PRINT: Initializing logger...')
    global logger
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    # set higher logging level for httpx to avoid all GET and POST requests being logged
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)

    # Initialize transformers
    logger.info('Initializing captioner...')
    global g_captioner
    g_captioner = pipeline(
        "image-to-text",
        model="Salesforce/blip-image-captioning-base"
    )

    # Initialize the Selenium browser
    logger.info('Initializing browser...')
    global g_browser
    g_browser = scmd.init_browser(logger)

    # Initialize selenium browser for miniCPM visual prompter
    logger.info('Initializing visual prompt model (selenium)...')
    global g_minicpm_ses
    g_minicpm_ses = minicpm.Session(logger)
    # Test image.
    # g_minicpm_ses.set_img(
    #     '/home/dincio/code/vinted-bot/vinted_bot/imgs/dddbfca6-2a11-4d2c-ad5f-642e7c5d75e1.jpg'
    # )

    # Create the Application and pass it your bot's token.
    logger.info('Loading token...')
    application = Application.builder().token(
        Path('./token').read_text('utf8')
    ).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    async def tsearch_cmd(upd, ctx): return TEST_SEARCH_QUERY
    async def search_cmd(upd, ctx):
        await upd.message.reply_text('Eneter search query:')
        return SEARCH_QUERY
    def gen_img_msg(product, idx, detailed=False):
        global g_captioner, g_minicpm_ses
        # Generate and cache img description.
        if 'imgs' not in product:
            product['imgs'] = [None for _ in product['img-links']]
            product['img-quick-descs'] = [None for _ in product['img-links']]
            product['img-descs'] = [None for _ in product['img-links']]
        if product['imgs'][idx] == None:
            img_path = Path(f'./imgs/{uuid.uuid4()}.jpg').resolve()
            wget.download(product['img-links'][idx], str(img_path))
            product['imgs'][idx] = img_path
            # img = open(img_path, 'rb').read()
            # product['img-descs'][idx] = g_captioner(product['img-links'])[0][0]['generated_text']
            product['img-quick-descs'][idx] = g_captioner(
                product['img-links'][idx]
            )
        # Generate and cache detailed img description
        if detailed and product['img-descs'][idx] == None:
            g_minicpm_ses.set_img(product['imgs'][idx])
            product['img-descs'][idx] = g_minicpm_ses.send_prompt(
                prompt='Describe this piece of clothing in details.',
                sleep_t=5,
                wait_for_msg_to_complete_t=10
            )
        # Compose msg based on required level of details
        if detailed:
            return product['img-links'][idx] + '\n\n' + str(product['img-descs'][idx])
        else:
            return product['img-links'][idx] + '\n\n' + str(product['img-quick-descs'][idx])
    def get_product_raw_info(product):
        global g_browser
        # Just a cache.
        if 'img-links' not in product:
            logger.info('Caching image links...')
            product['img-links'] = scmd.extract_product_info(g_browser, product['link'])
            return gen_img_msg(product, 0)
        else:
            return gen_img_msg(product, 0)
    def get_product_detailed_info(product):
        global g_browser
        # Just a cache.
        if 'img-links' not in product:
            logger.info('Caching image links...')
            product['img-links'] = scmd.extract_product_info(g_browser, product['link'])
            return gen_img_msg(product, 0, detailed=True)
        else:
            return gen_img_msg(product, 0, detailed=True)
    async def next_cmd(upd, ctx):
        global g_cur_list
        global g_cursor
        if g_cursor == len(g_cur_list) - 1:
            await upd.message.reply_text('Hit end of product list.')
            return
        g_cursor += 1
        await upd.message.reply_text('Extracting product info...')
        reply_txt = get_product_raw_info(g_cur_list[g_cursor])
        await upd.message.reply_text(reply_txt)
        return TOP_COMMANDS
    async def prev_cmd(upd, ctx):
        global g_cur_list
        global g_cursor
        if g_cursor == 0:
            await upd.message.reply_text('Hit beginning of product list.')
            return
        g_cursor -= 1
        await upd.message.reply_text('Extracting product info...')
        reply_txt = get_product_raw_info(g_cur_list[g_cursor])
        await upd.message.reply_text(reply_txt)
        return TOP_COMMANDS
    async def details_cmd(upd, ctx):
        global g_cur_list
        global g_cursor
        await upd.message.reply_text('Extracting detailed description...')
        reply_txt = get_product_detailed_info(g_cur_list[g_cursor])
        await upd.message.reply_text(reply_txt)
        return TOP_COMMANDS
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOP_COMMANDS: [
                CommandHandler('tsearch', tsearch_cmd),
                CommandHandler('search', search_cmd),
                CommandHandler('next', next_cmd),
                CommandHandler('prev', prev_cmd),
                CommandHandler('details', details_cmd)
            ],
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)],
            TEST_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_search_query)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info('Starting bot...')
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()