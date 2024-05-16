## Run selenium and chrome driver to scrape data from cloudbytes.dev
import time
import os.path
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

def search_products(arg_query, logger):
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
    
    # Get page and accept cookies
    browser.get('https://www.vinted.it')
    # browser.find_element(By.ID, 'onetrust-reject-all-handler').click()
    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="onetrust-reject-all-handler"]'))).click()
    logger.info('Cookies rejected')
    
    # Extract search bar
    # search_input = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.ID, 'search_text')))
    # search_input = browser.find_elements(By.ID, 'search_text')[1]
    search_inputs = browser.find_elements(By.XPATH, '//input[@id="search_text" and @name="search_text"]')
    logger.info(f'found {len(search_inputs)} search inputs, using the first')
    search_input = search_inputs[0]
    logger.info(f'search_input.tag_name [name: {search_input.tag_name}]')
    
    # Send test query
    # ActionChains(browser).move_to_element(search_input).click().send_keys('Jeans uomo').send_keys(Keys.ENTER).perform()
    # search_input.click()
    search_input.send_keys(arg_query)
    search_input.send_keys(Keys.ENTER)
    logger.info('Sent test query')
    
    # Extract all items resulting from the search
    q_results = browser.find_elements(By.XPATH, "//div[@data-testid='grid-item' and @class='feed-grid__item']")
    q_sellers = []
    q_products = []
    logger.info(f'Found {len(q_results)} results to query')
    for product in q_results:
            seller_link, product_link = product.find_elements(By.XPATH, ".//a[@href]")[0:2]
            q_sellers.append(seller_link.get_attribute('href'))
            q_products.append(product_link.get_attribute('href'))
    
    # Quit
    # time.sleep(10)
    # browser.quit()

    return q_sellers, q_products