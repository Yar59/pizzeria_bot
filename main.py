import argparse
from pprint import pprint

from environs import Env

from moltin_tools import (
    load_menu_moltin,
    load_addresses_moltin,
    get_api_key,
    get_products,
    create_flow,
    create_flow_field
)


def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
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
        load_menu_moltin(api_key, moltin_base_url, menu_path)
        pprint(get_products(moltin_base_url, api_key))

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
        load_addresses_moltin(api_key, moltin_base_url, addresses_path)


if __name__ == '__main__':
    main()
