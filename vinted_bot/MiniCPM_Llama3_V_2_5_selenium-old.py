import time

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

def init_browser(logger=None):
    # Setup chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Ensure GUI is off
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


def send_prompt(browser, prompt, logger=None, sleep_t=5):
    if logger:
        info = lambda s: logger.info(s)
    else:
        info = print

    text_input = WebDriverWait(
        browser, 120
    ).until(
        EC.element_to_be_clickable((By.XPATH, '//textarea[@data-testid="textbox"]'))
    )
    info(f'Found text input: {text_input}')

    text_input.send_keys(prompt)
    text_input.send_keys(Keys.ENTER)

    msgs_n = None
    while True:
        msgs = browser.find_elements(By.XPATH, '//div[@class="message-row bubble bot-row svelte-wnhv21"]')
        if msgs_n and len(msgs) > msgs_n:
            response = msgs[-1].find_elements(By.XPATH, '//p')[-1].get_attribute('innerHTML')
            info(f'Prompt response: {response}')
            return response
        else:
            msgs_n = len(msgs)
            info(f'Waiting for new msgs in wait of prompt response (num: {len(msgs)})')
            time.sleep(sleep_t)


if __name__ == '__main__':
    browser = init_browser()
    
    # input('Waiting...')
    # iframes = browser.find_elements(By.TAG_NAME, 'iframe')
    # print([x.get_attribute('src') for x in iframes])

    print('Searching file input...')
    # file_input = WebDriverWait(browser, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="file-upload"]')))
    file_input = WebDriverWait(
        browser, 120
    ).until(
        EC.presence_of_element_located((By.XPATH,'//input[@data-testid="file-upload"]'))
    )

    print(f'img input: {file_input}')

    file_input.send_keys('/home/dincio/code/tst-img/tst_img/img.jpg')
    awk_msg = WebDriverWait(browser, 120).until(
        EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Image uploaded successfully, you can talk to me now')]"))
    )
    print(f'Awk received: {awk_msg}')

    response = send_prompt(browser, 'Describe the image in many details, with particular attention to any clothing it contains')
    print(f'Response: {response}')
    while True:
        prompt = input('Prompt: ')
        response = send_prompt(browser, prompt)
        print(f'Response: {response}')