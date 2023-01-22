import argparse

from environs import Env

from moltin_tools import load_menu_moltin, load_addresses_moltin, get_api_key, get_products

from pprint import pprint


def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')
    moltin_base_url = env('MOLTIN_BASE_URL')
    api_key = get_api_key(moltin_base_url, moltin_client_id, moltin_client_secret)
    parser = argparse.ArgumentParser()
    parser.add_argument("--load_menu", help="id первой книги")
    parser.add_argument("--load_addresses", help="id первой книги")
    args = parser.parse_args()
    menu_path = args.load_menu
    addresses_path = args.load_addresses
    if menu_path:
        load_menu_moltin(api_key, moltin_base_url, menu_path)
    if addresses_path:
        pass
    pprint(get_products(moltin_base_url, api_key))


if __name__ == '__main__':
    main()
