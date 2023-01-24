import json
import logging
from datetime import datetime
from pprint import pprint
from urllib.parse import urljoin

import requests

_api_key = None
_expires = None


def get_api_key(base_url, client_id, client_secret):
    global _api_key
    global _expires
    url = urljoin(base_url, '/oauth/access_token')
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    current_time = datetime.now()
    timestamp = int(datetime.timestamp(current_time))
    if _expires:
        if timestamp < _expires:
            return _api_key

    response = requests.post(url, data=payload)
    response.raise_for_status()
    token_params = response.json()
    _api_key = token_params['access_token']
    _expires = token_params['expires']
    return _api_key


def get_products(base_url, api_key):
    url = urljoin(base_url, '/v2/products')
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_cart(base_url, api_key, product_id, quantity, user_id):
    url = urljoin(base_url, f'/v2/carts/{user_id}/items')
    headers = {'Authorization': f'Bearer {api_key}'}
    payload = {
        "data": {
            "type": "cart_item",
            "id": product_id,
            "quantity": int(quantity),
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart(base_url, api_key, user_id):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, f'/v2/carts/{user_id}/items')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(base_url, api_key, product_id):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, f'/catalog/products/{product_id}')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def fetch_image(base_url, api_key, image_id):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, f'/v2/files/{image_id}')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["link"]["href"]


def remove_item_from_cart(base_url, api_key, user_id, product_id):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, f'/v2/carts/{user_id}/items/{product_id}')
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def create_customer(base_url, api_key, user_id, email):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, '/v2/customers')
    payload = {
        "data": {
            "type": "customer",
            "name": user_id,
            "email": email,
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']['id']


def get_customer(base_url, api_key, customer_id):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, f'/v2/customers/{customer_id}')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def update_customer(base_url, api_key, customer_id, email):
    headers = {'Authorization': f'Bearer {api_key}'}
    url = urljoin(base_url, f'/v2/customers/{customer_id}')
    payload = {
        "data": {
            "type": "customer",
            "email": email,
        }
    }
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def load_menu_moltin(api_key, base_url, file_path):
    url = urljoin(base_url, '/v2/products')
    headers = {'Authorization': f'Bearer {api_key}'}
    with open(file_path, 'rb') as file:
        menu = json.load(file)
    for pizza in menu:
        payload = {
            "data": {
                "type": "product",
                "name": pizza['name'],
                "slug": f"pizza-{pizza['id']}",
                "sku": str(pizza['id']),
                "description": pizza['description'],
                "manage_stock": False,
                "price": [
                    {
                        "amount": pizza['price'],
                        "currency": "RUB",
                        "includes_tax": True
                    }
                ],
                "status": "live",
                "commodity_type": "physical"
            }
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            set_product_image(api_key, base_url, pizza['product_image']['url'], response.json()['data']['id'])
        except requests.exceptions.HTTPError:
            logging.exception('Ошибка при загрузке продукта')


def load_addresses_moltin(api_key, base_url, file_path):

    with open(file_path, 'rb') as file:
        addresses = json.load(file)

    url = urljoin(base_url, f'v2/flows/pizzeria/entries')
    headers = {'Authorization': f'Bearer {api_key}'}
    for address in addresses:
        payload = {
            'data': {
                'type': 'entry',
                'Address': address['address']['full'],
                'Alias': address['alias'],
                'Longitude': str(address['coordinates']['lon']),
                'Latitude': str(address['coordinates']['lat']),
            },
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            logging.exception('Ошибка при загрузке адреса')


def set_product_image(api_key, base_url, image_url, product_id):
    url = urljoin(base_url, '/v2/files')
    headers = {'Authorization': f'Bearer {api_key}'}
    files = {
        'file_location': (None, image_url),
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    image_id = response.json()['data']['id']
    url = urljoin(base_url, f'/v2/products/{product_id}/relationships/main-image')
    payload = {
        'data': {
            'type': 'main_image',
            'id': image_id,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()


def create_flow(api_key, base_url):
    url = urljoin(base_url, '/v2/flows')
    headers = {'Authorization': f'Bearer {api_key}'}
    payload = {
        'data': {
            'type': 'flow',
            'name': 'Pizzeria',
            'slug': 'pizzeria',
            'description': 'pizzeria model',
            'enabled': True,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']['id']


def create_flow_field(api_key, base_url, field_name, flow_id):
    url = urljoin(base_url, '/v2/fields')
    headers = {'Authorization': f'Bearer {api_key}'}
    payload = {
        'data': {
            'type': 'field',
            'name': field_name,
            'slug': field_name,
            'field_type': 'string',
            'description': 'pizzeria field',
            'required': True,
            'enabled': True,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id,
                    },
                },
            },
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']['id']
