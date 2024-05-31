import time

from pathlib import Path

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


class Session():
    def __init__(self, logger=None, headless=True):
        # Init logger
        self.info = from_logger(logger)
        info = self.info

        # Init browser
        self.browser = init_browser(logger, headless)

        # Get file input.
        info('Searching file input...')
        # file_input = WebDriverWait(browser, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="file-upload"]')))
        file_input = WebDriverWait(
            self.browser, 120
        ).until(
            EC.presence_of_element_located((By.XPATH,'//input[@data-testid="file-upload"]'))
        )
        info(f'img file input: {file_input}')
        self.img_input = file_input

        # Get prompt input.
        text_input = WebDriverWait(
            self.browser, 120
        ).until(
            EC.element_to_be_clickable((By.XPATH, '//textarea[@data-testid="textbox"]'))
        )
        info(f'Found text input: {text_input}')
        self.prompt_input = text_input

    def set_img(self, img_path):
        info = self.info

        self.img_input.send_keys(str(img_path.resolve()))
        awk_msg = WebDriverWait(self.browser, 120).until(
            EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Image uploaded successfully, you can talk to me now')]"))
        )
        info(f'Awk received: {awk_msg}\nImg set')

    def send_prompt(self, prompt, sleep_t=5, wait_for_msg_to_complete_t=7):
        info = self.info

        self.prompt_input.send_keys(prompt)
        self.prompt_input.send_keys(Keys.ENTER)

        msgs_n = None
        while True:
            msgs = self.browser.find_elements(By.XPATH, '//div[@class="message-row bubble bot-row svelte-wnhv21"]')
            if msgs_n and len(msgs) > msgs_n:
                info('Waiting for msg to complete...')
                time.sleep(wait_for_msg_to_complete_t)
                response = msgs[-1].find_elements(By.XPATH, '//p')[-1].get_attribute('innerHTML')
                info(f'Prompt response: {response}')
                return response
            else:
                msgs_n = len(msgs)
                info(f'Waiting for new msgs in wait of prompt response (num: {len(msgs)})')
                time.sleep(sleep_t)


def init_browser(logger=None, headless=True):
    # Setup chrome options
    chrome_options = Options()
    if headless: chrome_options.add_argument("--headless") # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1200x600")
    
    # Set path to chrome/chromedriver as per your configuration
    chrome_options.binary_location = f"./chrome-linux64/chrome"
    webdriver_service = Service(f"./chromedriver-linux64/chromedriver")
    
    # Initialize the Firefox WebDriver with WebDriverManager
    # browser = webdriver.Firefox()
    browser = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    browser.implicitly_wait(10)

    # Navigate to website.
    browser.get('https://openbmb-minicpm-llama3-v-2-5.hf.space/')

    # Go to website and reject cookies
    # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="onetrust-reject-all-handler"]'))).click()
    # logger.info('Cookies rejected')
    return browser


def from_logger(logger):
    if logger: info = lambda s: logger.info(s)
    else: info = print

    return info


if __name__ == '__main__':
    ses = Session(headless=False)

    ses.set_img('img.jpg')

    response = ses.send_prompt('Describe the shirt in details')
    print(response)
    while True:
        response = ses.send_prompt(input('Prompt: '))
        print(response)