import argparse
import logging
import requests
from environs import Env

from moltin_tools import (
    load_menu_moltin,
    load_addresses_moltin,
    get_api_key,
    create_flow,
    create_flow_field
)


def main():
    env = Env()
    env.read_env()
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')
    moltin_base_url = env('MOLTIN_BASE_URL')
    api_key = get_api_key(moltin_base_url, moltin_client_id, moltin_client_secret)
    parser = argparse.ArgumentParser()
    parser.add_argument("--load_menu", help="загрузить меню(укажите адрес файла)")
    parser.add_argument("--load_addresses", help="загрузить адреса пиццерий(укажите адрес файла)")
    parser.add_argument("--create_pizzeria_flow", help="создать flow для пиццерии", action='store_true')
    args = parser.parse_args()
    menu_path = args.load_menu
    addresses_path = args.load_addresses

    if menu_path:
        try:
            load_menu_moltin(api_key, moltin_base_url, menu_path)
        except requests.exceptions.HTTPError:
            logging.exception('Ошибка при загрузке продукта')

    if args.create_pizzeria_flow:
        flow_id = create_flow(api_key, moltin_base_url)
        flow_fields = [
            'Address',
            'Alias',
            'Longitude',
            'Latitude',
        ]
        for field in flow_fields:
            create_flow_field(api_key, moltin_base_url, field, flow_id)

    if addresses_path:
        try:
            load_addresses_moltin(api_key, moltin_base_url, addresses_path)
        except requests.exceptions.HTTPError:
            logging.exception('Ошибка при загрузке адреса')
            

if __name__ == '__main__':
    main()
