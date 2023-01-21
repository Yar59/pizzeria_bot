import argparse

from environs import Env

from moltin_tools import load_menu_moltin, load_addresses_moltin


def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')
    moltin_base_url = env('MOLTIN_BASE_URL')
    parser = argparse.ArgumentParser()
    parser.add_argument("--load_menu", help="id первой книги")
    parser.add_argument("--load_addresses", help="id первой книги")
    args = parser.parse_args()
    menu_path = args.load_menu
    addresses_path = args.load_addresses
    if menu_path:
        pass
    if addresses_path:
        pass


if __name__ == '__main__':
    main()
