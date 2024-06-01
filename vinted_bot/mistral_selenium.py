import time
import re
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
        self.info = logger.info if logger else print
        info = self.info

        # Init browser
        self.browser = init_browser(logger, headless)

    def login(self):
        info = self.info

        # Set username.
        login_input = WebDriverWait(
            self.browser, 120
        ).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id=":Rclkn:" and @name="identifier" and @type="text"]'))
        )
        info(f'Login buttons: {login_input}')
        time.sleep(2)
        login_input.send_keys('dincio.montesi@proton.me')

        # Set PW.
        pw_input = WebDriverWait(
            self.browser, 120
        ).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id=":Rklkn:" and @name="password" and @type="password"]'))
        )
        info(f'Login buttons: {pw_input}')
        time.sleep(2)
        pw_input.send_keys(Path('./auth/mistral-pw').read_text())

        # Click login button.
        login_button = WebDriverWait(
            self.browser, 120
        ).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @name="method" and @value="password"]'))
        )
        info(f'Login buttons: {login_button}')
        time.sleep(2)
        login_button.click()

    def send_prompt(self, prompt, sleep_t=5, wait_for_msg_to_complete_t=10):
        info = self.info

        # Wait for prompt input to be loaded.
        prompt_input = WebDriverWait(
            self.browser, 120
        ).until(
            EC.visibility_of_element_located((By.XPATH, '//textarea[@placeholder="Ask anything!"]'))
        )
        info(f'Prompt input: {prompt_input}')
        time.sleep(2)

        ActionChains(self.browser).send_keys(prompt).send_keys(Keys.ENTER).perform()

        # Send prompt
        # <div id="39af532b-7737-450b-af5f-88b9c9fd3168">
        id_form = r'^[0-9a-f]{1,16}-[0-9a-f]{1,16}-[0-9a-f]{1,16}-[0-9a-f]{1,16}-[0-9a-f]{1,16}$'
        msgs_n = None
        while True:
            msgs = self.browser.find_elements(By.XPATH, '//div[@id]')
            msgs = [
                m
                for m in msgs
                if re.match(id_form, m.get_attribute("id"))
            ]
            info(f'Msgs: {msgs}')
            if msgs_n and len(msgs) > msgs_n:
                info('Waiting for msg to complete...')
                time.sleep(wait_for_msg_to_complete_t)
                response = '\n'.join(
                    p.get_attribute('innerHTML')
                    for p in msgs[-1].find_elements(By.TAG_NAME, 'p')
                )
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
    browser.get('https://chat.mistral.ai')

    # Go to website and reject cookies
    # WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="onetrust-reject-all-handler"]'))).click()
    # logger.info('Cookies rejected')
    return browser


if __name__ == '__main__':
    ses = Session(headless=False)

    ses.login()

    while True:
        ses.send_prompt(input('Prompt: '))