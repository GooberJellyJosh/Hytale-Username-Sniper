##
##--IMPORTS--
# Standard
import time
import json
import os
import random as rd
import tempfile
import shutil
from pathlib import Path
from urllib.parse import uses_netloc
# Third party
from exceptiongroup import catch
from selenium.common import TimeoutException
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


##--FUNCTIONS--
def import_user_config():
    """
        Imports data from the user configuration file and the list of names.
       :return: list_of_names, email, password, min_delay, max_delay
    """
    list_of_names, email, password, min_delay, max_delay = [], "", "", 0, 0

    with open("../Config/user_config", "r") as f:
        config = json.load(f)
        email, password, min_delay, max_delay = config["Email"], config["Password"], config["Minimum_Delay"], config["Maximum_Delay"]

    with open("../Config/name_list", "r") as f:
        list = json.load(f)
        list_of_names = [name for name in list]

    print(f"Imported {len(list_of_names)} names.")
    return list_of_names, email, password, min_delay, max_delay


def start_chrome_with_clean_profile():
    """
    Creates a clean browser instance with clear cache and cookies.
    """
    profile_dir = tempfile.mkdtemp()
    opts = Options()
    opts.add_argument(f"--user-data-dir={profile_dir}")
    opts.add_experimental_option("detach", True)
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



def login(email, password):
    element = driver.find_elements(By.XPATH, '//p[contains(text(), "send a verification code to your email address.")]')
    if len(element) == 0:
        try:
            # Finds and clicks "login with email" button
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/div[1]/div/button'))
            )
            login_with_email_button = driver.find_element(By.XPATH, '//*[@id="login-form"]/div[1]/div/button')
            login_with_email_button.click()

            # Enters email and password
            time.sleep(1)
            WebDriverWait(driver, 10).until(
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

    # Finds and clicks "change username" button
    time.sleep(2)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Change username']"))
        )
        change_username_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Change username']")
        change_username_button.click()
    except:
        print("Error: Couldn't find 'Change Username' button.")



total_name_change_attempts = 0

def change_Name(list_of_names, min_delay, max_delay):
    global total_name_change_attempts
    rate_limit_delay = 7
    while True:
        for name in list_of_names:
            # Finds input element and sends username
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]'))
            )
            input_element = driver.find_element(By.XPATH, '//*[@id="modal-0e4d3ecc-1c04-4277-98b8-47b5d8a01a21"]')
            try:
                input_element.clear()
                if input_element.get_attribute("value") == "":
                    input_element.send_keys(name)
            except:
                pass
            # Checks if captcha is visible and, if it is, waits until the captcha is filled out.
            captcha = driver.find_elements(By.XPATH, '//*[@id="turnstile-modal-title"]')
            if captcha:
                WebDriverWait(driver, 120).until_not(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="turnstile-modal-title"]'))
                )


            # Tries to get response code
            total_name_change_attempts += 1
            response_code = 0
            try:
                response_code = driver.requests[-1].response.status_code
            except:
                response_code = "No response code found."

            print(f"Attempted to change name to: {name}.    |   Response code: {response_code}  |   Attempt {total_name_change_attempts}.   |   Current rate limit delay: {rate_limit_delay}")

            # Sleeps if response code was unsuccessful.
            # sleep time adapts according to previous response codes.
            if response_code >= 400:
                rate_limit_delay += 2
                time.sleep(rate_limit_delay)
            elif response_code == 200 and rate_limit_delay >= 1:
                rate_limit_delay -= 1

            # Exits loop after a certain amount of attempts.
            if (total_name_change_attempts % 100000 == 0):
                return


            # Sleeps for random durations according to the delays set in the user configuration file.
            time.sleep(rd.randint(min_delay, max_delay))


##---MAIN---

# Imports data
URL = "https://accounts.hytale.com/profiles"
list_of_names, email, password, min_delay, max_delay = import_user_config()

while True:
    # Opens browser and loads website
    service  = Service(executable_path="chromedriver.exe")
    driver, prof = start_chrome_with_normal_profile()
    driver.get(URL)
    time.sleep(3)

    # Tries to login
    try:
        login(email, password)
    except:
        print("Error: Couldn't login.")

    # Waits for user to start the bot
    input("Press any key to start bot...")

    # Tries to change username
    try:
        change_Name(list_of_names, min_delay, max_delay)
    except:
        print("Error: change_name function didn't work.")

    print(f"Total name change attempts: {total_name_change_attempts}")
    shutil.rmtree(prof, ignore_errors=True)