import selenium_cmds as cmds
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    browser = cmds.init_browser(logger)
    print(cmds.extract_product_info(
        browser,
        'https://www.vinted.it/items/4508508551-jeans-donna-rifle?referrer=catalog'
    ))