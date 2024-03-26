import os
from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext)
import configparser
import logging
from ChatGPT_HKBU import HKBU_ChatGPT
import requests
import geopy
from geopy.geocoders import Nominatim
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


def main():
    # Load your token and create an Updater for your Bot
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(token=config['TELEGRAM']['ACCESS_TOKEN'], use_context=True)
    dispatcher = updater.dispatcher

    service_account_key = config.get('FIREBASE', 'SERVICE_ACCOUNT_KEY')
    database_url = config.get('FIREBASE', 'DATABASE_URL')
    cred = credentials.Certificate(service_account_key)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
    })

    # You can set this logging module, so you will know when and why things do not work as expected Meanwhile, update your config.ini as:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # register a dispatcher to handle message: here we register an echo dispatcher
    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    # dispatcher.add_handler(echo_handler)

    global chatgpt

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("parking", get_location))
    dispatcher.add_handler(CommandHandler("address", search_parking))
    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, search_parking))

    # dispatcher for chatgpt

    chatgpt = HKBU_ChatGPT(config)
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), handle_user_input)
    dispatcher.add_handler(chatgpt_handler)

    # To start the bot:
    updater.start_polling()
    updater.idle()


def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)


def handle_user_input(update, context):
    user_input = update.message.text

    # Determine if user input is a command to search for a parking lot
    if user_input.lower() == "parking":
        get_location(update, context)
    else:
        equiped_chatgpt(update, context)


def get_location(update, context):
    response = "Please enter your address(Please enter via the /address command): "
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def search_parking(update, context):
    api_key = "AIzaSyD4rxqPhTz5wCaEfbamZkvrcu6uU6SMqyE"
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    user_address = update.message.text.replace('/address', '').strip()
    geolocator = Nominatim(user_agent="my_chatbot")
    location = geolocator.geocode(user_address)
    user_location = f"{location.latitude},{location.longitude}"

    params = {
        "key": api_key,
        "location": user_location,
        "radius": 1000,  # 搜索半径（单位：米）
        "keyword": "parking",  # 关键词为停车场
        "language": "zh-HK",  # 搜索结果语言为中文（香港）
        "region": "hk"  # 限制搜索区域为香港
    }

    response = requests.get(url, params=params)
    data = response.json()
    ref = db.reference('server/saving-data/fireblog')
    parking_ref = ref.child('parking')

    if data.get("status") == "OK":
        results = data.get("results")
        for result in results:
            name = result.get("name")
            address = result.get("vicinity")
            new_parking_ref = parking_ref.push()
            # 生成唯一的键
            new_parking_ref.set({
                'name': result.get("name"),
                'address': result.get("vicinity")
            })
            response = f"parking: {name}, parking lot location: {address}"
            context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    else:
        response = "There's no parking within one kilometer of here."
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def equiped_chatgpt(update, context):
    global chatgpt
    reply_message = chatgpt.submit(update.message.text)
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Helping you helping you.')


def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    ref = db.reference('/server/saving-data/fireblog')

    try:
        msg = context.args[0]  # /add keyword <-- this should store the keyword
        ref.child(msg).transaction(lambda current_value: (current_value or 0) + 1)
        value = ref.child(msg).get()
        if value is not None:
            update.message.reply_text('You have said ' + msg + ' for ' + str(value) + ' times.')
        else:
            update.message.reply_text('You have not said ' + msg + ' before.')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')


def hello(update, context):
    """Send a message when the command /hello is issued."""
    name = context.args[0] if len(context.args) > 0 else "Unknown"
    response = f"Good day, {name}!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)


if __name__ == '__main__':
    main()
