##
##--IMPORTS--
# Standard
import time
import json
import os
import random as rd
import tempfile
import shutil
from operator import index
from pathlib import Path
from urllib.parse import uses_netloc
# Third party
from exceptiongroup import catch
from selenium.common import TimeoutException
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


##--FUNCTIONS--
def import_user_config():
    """
        Imports data from the user configuration file and the list of names.
       :return: list_of_names, email, password, min_delay, max_delay, rate_limit_delay
    """
    with (open("../Config/user_config", "r") as f):
        config = json.load(f)
    with open("../Config/name_list", "r") as f:
        dict = json.load(f)
        list_of_names = list(dict.keys())
    print(f"Imported {len(list_of_names)} names.")
    print(f"min_delay: {config['Minimum_Delay']}, max_delay: {config['Maximum_Delay']}, rate_limit_delay: {config['Rate_Limit_Delay']}")

    return (
        list_of_names,
        config['Email'],
        config['Password'],
        config['Minimum_Delay'],
        config['Maximum_Delay'],
        config['Rate_Limit_Delay'],
        config['Proxy'],
    )


def start_chrome_with_clean_profile():
    """
    Creates a clean browser instance with clear cache and cookies.
    """
    profile_dir = tempfile.mkdtemp()
    opts = Options()
    opts.add_argument(f"--user-data-dir={profile_dir}")
    opts.add_argument("--disable-webrtc")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=opts)
    return driver, profile_dir

def start_chrome_with_normal_profile():
    """
    Opens a browser instance using the stored cache and cookies.
    """
    profile_dir = os.path.abspath("Assets/chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)
    opts = Options()
    opts.add_argument(f"--user-data-dir={profile_dir}")
    opts.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=opts)
    return driver, profile_dir

def start_chrome_with_proxy(proxy):
    """
    Opens a browser instance with a clean cache and cookies, and a proxy.
    :param proxy: proxy formatted as server:port:username:password
    """
    profile_dir = tempfile.mkdtemp()

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("detach", True)

    seleniumwire_options = {
        "proxy": {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}" ,
            "no_proxy": "localhost,127.0.0.1"
        }
    }

    driver = webdriver.Chrome(
        options=chrome_options,
        seleniumwire_options=seleniumwire_options
    )

    return driver, profile_dir


def login(email, password):
    element = driver.find_elements(By.XPATH, '//p[contains(text(), "send a verification code to your email address.")]')
    if len(element) == 0:
        try:
            # Finds and clicks "login with email" button
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/div[1]/div/button'))
            )
            login_with_email_button = driver.find_element(By.XPATH, '//*[@id="login-form"]/div[1]/div/button')
            login_with_email_button.click()

            # Enters email and password
            time.sleep(1)
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "identifier"))
                and
                EC.presence_of_element_located((By.ID, "password"))
            )
            email_input = driver.find_element(By.ID, "identifier")
            password_input = driver.find_element(By.ID, "password")
            email_input.send_keys(email)
            password_input.send_keys(password + Keys.ENTER)
        except:
            print("Error: Couldn't find login buttons or inputs.")

def input_name(name):
    input_element = driver.find_element(By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]')
    input_element.clear()
    WebDriverWait(driver, 10).until(
        lambda a: input_element.get_attribute("value") == ""
    )
    input_element.clear()

    time.sleep(rd.uniform(0.1, 0.5))
    for letter in name:
        input_element.send_keys(letter)
        time.sleep(0.1)
    time.sleep(0.2)

def name_is_correct(name):
    input_element = driver.find_element(By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]')
    if input_element.get_attribute("value") == name:
        return True
    else:
        return False


def change_Name(list_of_names, min_delay, max_delay, rate_limit_delay):
    total_name_change_attempts = 0
    index = 0
    while index <= len(list_of_names):
        name = list_of_names[index]
        # Finds input element and sends username
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]'))
            # EC.presence_of_element_located((By.ID, "modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"))
        )
        try:

            input_name(name)
            if not name_is_correct(name):
                input_element = driver.find_element(By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]')
                input_element.clear()
                input_name(name)

            # submit_button.click()

            # time.sleep(rd.uniform(0.1, 0.5))
            # input_element.send_keys(name)
            # time.sleep(0.2)
            # submit_button.click()
        except:
            pass

        # Checks if captcha is visible and, if it is, waits until the captcha is filled out.
        try:
            captcha_element = driver.find_element(By.XPATH, '//span[normalize-space()="Verify you are human"]')
            if captcha_element:
                WebDriverWait(driver, 120).until(
                    EC.invisibility_of_element_located(By.XPATH, '//span[normalize-space()="Verify you are human"]')
                )
                time.sleep(7)
        except:
            pass


        # Tries to get response code
        total_name_change_attempts += 1
        response_code = 0
        while response_code == 0:
            try:
                response_code = driver.requests[-1].response.status_code
            except:
                pass



        # Sleeps if response code was unsuccessful.
        # sleep time adapts according to previous response codes.
        input_element = driver.find_element(By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]')
        random_delay = rd.uniform(min_delay, max_delay)
        total_delay = 0
        attempted_name = input_element.get_attribute("value")
        if response_code >= 400:
            total_delay += (rate_limit_delay)
            print_info(attempted_name, response_code, total_name_change_attempts, total_delay)
            time.sleep(rate_limit_delay)
        elif 300 < response_code < 400:
            total_delay += random_delay
            print_info(attempted_name, response_code, total_name_change_attempts, total_delay)
            time.sleep(random_delay)
        elif response_code == 200:
            total_delay += random_delay
            print_info(attempted_name, response_code, total_name_change_attempts, total_delay)
            time.sleep(random_delay)
            if name_is_correct(name):
                if is_still_available():
                    click_submit_button()
                    input_element.send_keys(Keys.ENTER)
                    print("Tried to submit.")
                else:
                    index += 1
            else:
                print("Error: incorrect input.")

        else:
            total_delay += random_delay
            print_info(name, response_code, total_name_change_attempts, total_delay)
            time.sleep(random_delay)


def is_still_available():
    try:
        status_element = driver.find_element(By.XPATH, '//*[@id="game-profiles"]/div/div[2]/div/form/div[2]/p')
        status = status_element.text
        print(f"Status: {status}")
        if status != "Username is already in use":
            return True
        else:
            return False
    except:
        return False

def click_submit_button():
    try:
        submit_button = driver.find_element(By.XPATH, '//*[@id="game-profiles"]/div/div[2]/div/form/button')
        submit_button.click()
    except:
        pass

def get_ip(driver):
    try:
        driver.get("https://api.ipify.org")
        return driver.page_source.split('>')[6].split('<')[0]
    except:
        return "Error: Couldn't get IP."

def print_info(name, response_code, total_name_change_attempts, total_delay):
    print(
        f"Attempted to change name to: {name}.    |   "
        f"Response code: {response_code}  |   "
        f"Attempt {total_name_change_attempts}.   |   "
        f"Delay: {total_delay}")


##---MAIN---

# Imports data
URL = "https://accounts.hytale.com/profiles"
list_of_names, email, password, min_delay, max_delay, rate_limit_delay, proxy = import_user_config()

try:
    while True:
        # Opens browser and loads website
        service  = Service(executable_path="chromedriver.exe")
        if proxy != "":
            driver, prof = start_chrome_with_proxy(proxy)
        else:
            driver, prof = start_chrome_with_normal_profile()

        # Gets the IP being used so you can ensure that the proxy worked
        print(f"IP: {get_ip(driver)}")


        # Opens website
        driver.get(URL)
        time.sleep(1)

        # Tries to login
        try:
            login(email, password)
        except:
            print("Error: Couldn't login.")

        # Waits for user to start the bot
        input("Press any key to start bot...")
        time.sleep(0)

        # Tries to change username
        try:
            change_Name(list_of_names, min_delay, max_delay, rate_limit_delay)
        except:
            print("Error: change_name function didn't work.")

        shutil.rmtree(prof, ignore_errors=True)
except Exception as e:
    input("Press any key to close the browser...")
