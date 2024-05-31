'''
This script was made for educational purposes only, any malicious of any kind or illegal use, and it's consequences are your own responsibility.

'''
import json
import logging
import os
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import configparser
import random

# Color codes
HEADER = '\033[95m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
DARKCYAN = '\033[36m'
UNDERLINE = '\033[4m'
PURPLE = '\033[95m'
ENDC = '\033[0m'

jiraffe = (f"""{YELLOW}\

                                       ._ o o               ⣀⣤⠄⣰⣾⣿⣿⣷⡄
        JIRAFFE SCRAPPERo.ooO_         \_`-)|_        ⠰⣶⣿⡄⠀⣿⣿ ⢰⣿⣏⠀⠘⣿⣿
        By FOX_TETRIS               ,""       \       ⠀⠹⣿⣷⡀⢹⣿ ⢸⣿⣿⡿⠿⠟⠛
                                  ,"  ## |   ಠ ಠ.       ⠹⣿⣷⣸⣿  ⢿⣿⣦⣀⣀⣤⡄
                                ," ##   ,-\__    `.      ⠙⣿⣿⣿⠀  ⠙⠿⠿⠿⠟⠃
                              ,"       /     `--._;)     ⠀⢘⣿⡟⠀
             IT'S SIMPLE    ,"     ## /                  ⣠⣾⣿⠇⠀
     IT WORKS             ,"   ##    /                  ⠘⠿⠋
                    """ + ENDC)

config = None

exclude_keys = ['payloadtype']

sep = "-"*40
sept = "\\"*40 + "\n"

async def load_config():
    global config, url_get, url_post, payload_type, token_selector, data_selector

    if config is None:
        config = configparser.ConfigParser()
        await asyncio.to_thread(config.read, 'config.ini')
        if not config.has_section('Settings'):
            config.add_section('Settings')
            config.set('Settings', 'RandomDelay', 'true') # True to add random delay, false otherwise
            config.set('Settings', 'AgentRotator', 'true') # True to rotate user agent, false otherwise

        if not config.has_section('URLs'):
            config.add_section('URLs')
            config.set('URLs', 'URL_GET', 'https://example.com') # The URL for GET requests
            config.set('URLs', 'URL_POST', 'https://example.com/example') # The URL for POST requests

        if not config.has_section('Selectors'):
            config.add_section('Selectors')
            config.set('Selectors', 'token_selector_html', 'input[name="_tokenid"]') # CSS selector for the token
            config.set('Selectors', 'data_selector_html', 'input[id="elementid"]') # CSS selector for the data

        if not os.path.isfile('config.ini'):
            await asyncio.to_thread(lambda: config.write(open('config.ini', 'w')))

    url_get = config.get('URLs', 'URL_GET')
    url_post = config.get('URLs', 'URL_POST')
    token_selector = config.get('Selectors', 'token_selector_html')
    data_selector = config.get('Selectors', 'data_selector_html')

    # Load payload from JSON file
    payload_file = 'payload.json'
    payload_data = None
    payload_type = None

    # Check if the JSON file and the config file have been created successfully
    json_file_created = os.path.isfile('payload.json')
    config_file_created = os.path.isfile('config.ini')

    if not os.path.isfile(payload_file):
        # Create default payload data
        default_payload_data = {
            "payload_type": "(name, email, etc.)",
            "payload_data": {
                "example_data": "(address, phone number, etc.)"
                # Add more payload data as needed
            }
        }
        await asyncio.to_thread(lambda: json.dump(default_payload_data, open(payload_file, 'w'), indent=4))
        print(f"Created default json payload file at {payload_file}")
    else:
        payload_data = await asyncio.to_thread(json.load, open(payload_file))
        payload_type = payload_data['payload_type']

    print(jiraffe)

    return config, payload_type, payload_data, json_file_created, config_file_created

async def generate_mobile():
    mobile_prefixes = [
        '050', '052', '054', '055', '056', '058', '059', '070', '076', '077', '078', '079'
    ]
    mobile_suffix = str(random.randint(10000000, 99999999))
    mobile_number = f"{random.choice(mobile_prefixes)}{mobile_suffix}"
    return mobile_number

async def download_user_agents():
    user_agents_file = 'user_agents.txt'
    url = "https://gist.githubusercontent.com/pzb/b4b6f57144aea7827ae4/raw/cf847b76a142955b1410c8bcef3aabe221a63db1/user-agents.txt"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(user_agents_file, 'w') as f:
                    await f.write(await response.text())
            else:
                print(f"Failed to download user agents file from {url} with status code: {response.status}")

async def check_and_download_user_agents():
    if not os.path.isfile('user_agents.txt'):
        await download_user_agents()

async def get_data(session, payload, headers, config):
    try:
        # Send get request to get token
        async with session.get(url_get, headers=headers) as res:
            res.raise_for_status()  # Raise an exception if the HTTP request returned an error
            text = await res.text()
        token_selector = config['Selectors']['token_selector_html']
        data_selector = config['Selectors']['data_selector_html']
        # Parse HTML response for the token
        soup = BeautifulSoup(text, features="lxml")
        token = soup.select_one(token_selector)['value']
        payload['_token'] = token

        # Send post request with token
        async with session.post(url_post, data=payload, headers=headers) as activate:
            activate.raise_for_status()  # Raise an exception if the HTTP request returned an error
            activate_text = await activate.text()

        # Find the element by id
        data_input = BeautifulSoup(activate_text, "lxml").select_one(data_selector)
        if data_input is not None:
            data = data_input["value"]
            return data
        else:
            raise Exception("Failed to get data")

    # MMyes error handling here
    except aiohttp.ClientError as e:
        logging.error(e)
        raise Exception(f"Post request failed: {e}")

async def save_data(data):
    async with aiofiles.open('data.txt', mode='a') as f:
        await f.write(data + '\n')

def get_positive_number(prompt, default=None):
    while True:
        try:
            if default is not None:
                input_value = input(f"{prompt} [Default: {YELLOW}{default}{ENDC}]: ").strip()
            else:
                input_value = input(prompt).strip()

            if not input_value and default is not None:
                print(f"Using default value: {YELLOW}{default}{ENDC}")
                return default

            number = int(input_value)
            if number > 0:
                return number
            else:
                print(f"{RED}Invalid input. Please enter a positive number.{ENDC}")
        except ValueError:
            print(f"{RED}Invalid input. Please enter a valid number.{ENDC}")

def print_config():
    print(f"{BOLD}{PURPLE}{UNDERLINE}CONFIG SETTINGS:{ENDC}")
    if payload_type and payload_type.strip():
        print(f"{BOLD}{HEADER}Payload Type:{ENDC} {YELLOW}{payload_type}{ENDC}")
    else:
        print(f"{BOLD}{HEADER}Payload Type:{ENDC} {RED}Not specified.{ENDC}")

    for section in config.sections():
        for key, value in config[section].items():
            if key not in exclude_keys:
                print(f"{BOLD}{HEADER}{key}:{ENDC} {YELLOW}{value}{ENDC}")

async def main():
    global config
    config_created = False
    if config is None:
        config_created = await asyncio.wait_for(load_config(), timeout=5)
        if not config_created:
            print("Error: Failed to create configuration file. Exiting...")
            return
    if config_created:
        print("Configuration files loaded...")

    # Download user agents
    await check_and_download_user_agents()

    # Display config settings
    print_config()

    # Load user agents from file
    user_agents_file = 'user_agents.txt'
    user_agents = []
    if os.path.isfile(user_agents_file):
        print(f"{BOLD}{PURPLE}Loaded user agents from {user_agents_file}...{ENDC}")
        with open(user_agents_file, 'r') as f:
            user_agents = [line.strip() for line in f]

    # Ask how many data elements the user wants to get
    num_of_data = None
    while num_of_data is None:
        try:
            num_of_data = get_positive_number(sept + f"{CYAN}Enter the number of elements you want to get:{ENDC} ")
            bulk = get_positive_number(f"{CYAN}Size of each bulk:{ENDC} ", default=30)
            sleep_time_min = get_positive_number(f"{CYAN}Enter the minimum sleep time between requests (seconds):{ENDC} ", default=20)
            sleep_time_max = get_positive_number(f"{CYAN}Enter the maximum sleep time between requests (seconds):{ENDC} ", default=30)
        except EOFError:
            print("Input interrupted. Exiting...")
            return

    # Run in a loop until the specified number is fetched
    fetched_data = 0
    async with aiohttp.ClientSession() as session:
        try:
            while fetched_data < num_of_data:
                sleep_time = round(random.uniform(sleep_time_min, sleep_time_max), 2)
                paload_params = await generate_mobile()
                headers = {'user-agent': random.choice(user_agents)}
                payload = {payload_type: paload_params} # Example with the random number generation
                print (sep)

                # Get token and data
                data = await get_data(session, payload, headers)
                if data is not None:
                    await save_data(data)
                    print(data)
                    fetched_data += 1
                    print(f"Fetched {fetched_data}/{num_of_data} elements")

                if fetched_data % bulk == 0 and fetched_data != num_of_data:
                    print(f"{CYAN}Sleeping for {sleep_time} seconds...{ENDC}")
                    await asyncio.sleep(sleep_time)  # Sleep for 5 seconds after every 30 requests

            success_message = f"\n{GREEN}All of {num_of_data} requested elements have been successfully fetched and saved.{ENDC}"
            print(success_message)

        except Exception as fetch:
            logging.error(fetch)
            fetch_message = f"\n{RED}Failed to fetch element.{ENDC}"
            print(fetch_message)

        finally:
            await session.close()
            exit_message = f"\n{GREEN}Exiting...{ENDC}"
            print(exit_message)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        interrupt_message = f"\n{RED}Interrupted by user. Exiting...{ENDC}"
        print(interrupt_message)