import logging
from enum import Enum, auto
from textwrap import dedent
from functools import partial
from pprint import pprint

import redis
import requests
from environs import Env
from redispersistence.persistence import RedisPersistence
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler
)

from moltin_tools import (
    get_api_key,
    get_products,
    get_cart,
    add_product_to_cart,
    get_product,
    fetch_image,
    remove_item_from_cart,
    create_customer
)

logger = logging.getLogger(__name__)


class States(Enum):
    start = auto()
    handle_menu = auto()
    handle_description = auto()
    handle_cart = auto()
    waiting_email = auto()


class Transitions(Enum):
    menu = auto()
    description = auto()
    cart = auto()
    order = auto()


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()["response"]["GeoObjectCollection"]["featureMember"]

    if not found_places:
        raise requests.exceptions.RequestException

    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
    return lat, lon


def start(update: Update, context: CallbackContext, base_url, api_key) -> int:
    query = update.callback_query

    products = get_products(base_url, api_key)
    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products
    ]
    keyboard.append(
        [
            InlineKeyboardButton('Корзина', callback_data=str(Transitions.cart)),
        ],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        query.answer()
        query.message.reply_text(
            text='Вусная питса:',
            reply_markup=reply_markup
        )
        query.message.delete()
    else:
        update.message.reply_text(
            text='Вусная питса:',
            reply_markup=reply_markup
        )

    return States.handle_menu


def cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_chat.id
    update.message.reply_text(
        'Надеюсь тебе понравился наш магазин!'
    )

    return ConversationHandler.END


def handle_menu(update: Update, context: CallbackContext, base_url, api_key) -> int:
    query = update.callback_query
    query.answer()
    user_id = update.effective_chat.id
    product_id = query['data']
    product = get_product(base_url, api_key, product_id)
    pprint(product)
    image_link = fetch_image(base_url, api_key, product['relationships']['main_image']['data']['id'])
    message = dedent(f'''
        {product["name"]}
        {product["description"]}
        Цена за кг: {product["price"][0]["amount"]}
    ''')
    keyboard = [
        [
            InlineKeyboardButton('Добавить в корзину', callback_data=f'1|{product_id}'),
        ],
        [
            InlineKeyboardButton('Корзина', callback_data=str(Transitions.cart)),
            InlineKeyboardButton('Назад', callback_data=str(Transitions.menu)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_photo(
        photo=image_link,
        caption=message,
        reply_markup=reply_markup,
    )
    query.message.delete()

    return States.handle_description


def handle_description(update: Update, context: CallbackContext, base_url, api_key) -> int:
    query = update.callback_query
    query.answer()
    quantity, product_id = query['data'].split('|')
    user_id = update.effective_chat.id
    add_product_to_cart(base_url, api_key, product_id, quantity, user_id)

    return States.handle_description


def handle_cart(update: Update, context: CallbackContext, base_url, api_key) -> int:
    query = update.callback_query
    query.answer()
    user_id = update.effective_chat.id
    if '|' in query['data']:
        action, product_id = query['data'].split('|')
        remove_item_from_cart(base_url, api_key, user_id, product_id)
    cart = get_cart(base_url, api_key, user_id)

    pprint(cart)

    fish_names_ids = {}
    total_cost = 0
    items_info = []
    for item in cart['data']:
        item_name = item['name']
        item_id = item['id']
        item_description = item['description']
        fish_names_ids[item_name] = item_id
        item_quantity = item['quantity']
        item_cost = item['value']['amount']
        total_cost += item_cost
        items_info.append(
            dedent(f'''
                {item_name}
                {item_description}
                {item_quantity} пицц на сумму {item_cost} руб.
                
            ''')
        )
    message = f'{"".join(items_info)}\nК оплате {total_cost} руб.'
    keyboard = [
        [InlineKeyboardButton(f'Удалить {name} из корзины', callback_data=f'del|{product_id}')]
        for name, product_id in fish_names_ids.items()
    ]
    keyboard.append(
        [
            InlineKeyboardButton('Меню', callback_data=str(Transitions.menu)),
            InlineKeyboardButton('Оформить заказ', callback_data=str(Transitions.order)),
        ],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(
        text=message,
        reply_markup=reply_markup,
    )
    query.message.delete()

    return States.handle_cart


def handle_order(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    if query['data'] == str(Transitions.order):
        message = 'Пришлите, пожалуйста, вашу электронную почту.'

    keyboard = [
        InlineKeyboardButton('Меню', callback_data=str(Transitions.menu)),
        InlineKeyboardButton('Корзина', callback_data=str(Transitions.cart)),
    ],
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
        text=message,
        reply_markup=reply_markup,
    )
    query.message.delete()

    return States.waiting_email


def handle_location(update: Update, context: CallbackContext, base_url, api_key) -> int:
    user_id = update.effective_chat.id
    if '@' in update.message.text:
        customer_email = update.message.text.strip()
        message = f'Записал Вашу почту {customer_email}'
        update.message.reply_text(
            text=message,
        )
        create_customer(base_url, api_key, user_id, message)
        next_state = ConversationHandler.END
        return next_state
    else:
        message = 'Это не похоже на почту, попробуйте еще раз.'
        update.message.reply_text(
            text=message,
        )

        return States.waiting_email


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_db = env('REDIS_DB', 0)
    redis_username = env('REDIS_USERNAME')
    redis_password = env('REDIS_PASSWORD')
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')
    moltin_base_url = env('MOLTIN_BASE_URL')
    api_key = get_api_key(moltin_base_url, moltin_client_id, moltin_client_secret)

    redis_db = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        # username=redis_username,
        # password=redis_password,
        decode_responses=True
    )
    persistence = RedisPersistence(redis_db)
    updater = Updater(token=tg_token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                'start',
                partial(start, base_url=moltin_base_url, api_key=api_key)
            ),
        ],
        states={
            States.handle_menu: [
                CallbackQueryHandler(
                    partial(handle_cart, base_url=moltin_base_url, api_key=api_key),
                    pattern=f'^{Transitions.cart}$'
                ),
                CallbackQueryHandler(
                    partial(handle_menu, base_url=moltin_base_url, api_key=api_key)
                )
            ],
            States.handle_description: [
                CallbackQueryHandler(
                    partial(start, base_url=moltin_base_url, api_key=api_key),
                    pattern=f'^{Transitions.menu}$'
                ),
                CallbackQueryHandler(
                    partial(handle_cart, base_url=moltin_base_url, api_key=api_key),
                    pattern=f'^{Transitions.cart}$'
                ),
                CallbackQueryHandler(
                    partial(handle_description, base_url=moltin_base_url, api_key=api_key)
                )
            ],
            States.handle_cart: [
                CallbackQueryHandler(
                    partial(start, base_url=moltin_base_url, api_key=api_key),
                    pattern=f'^{Transitions.menu}$'
                ),
                CallbackQueryHandler(
                    handle_order,
                    pattern=f'^{Transitions.order}$'
                ),
                CallbackQueryHandler(
                    partial(handle_cart, base_url=moltin_base_url, api_key=api_key)
                )
            ],
            States.waiting_email: [
                CallbackQueryHandler(
                    partial(start, base_url=moltin_base_url, api_key=api_key),
                    pattern=f'^{Transitions.menu}$'
                ),
                CallbackQueryHandler(
                    partial(handle_cart, base_url=moltin_base_url, api_key=api_key),
                    pattern=f'^{Transitions.cart}$'
                ),
                MessageHandler(Filters.text, partial(handle_email, base_url=moltin_base_url, api_key=api_key))
            ]
        },
        fallbacks=[
            CommandHandler('cancel', partial(cancel)),
            CommandHandler('start', partial(cancel)),
        ],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()

