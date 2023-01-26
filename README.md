# Пиццерия в телеграм
Бот для продажи пиццы в телеграм.
[Пример бота](https://t.me/pizza_s_maslom_bot)

## Установка
Перед использованием программы необходимо:
- Зарегистрироваться в сервисе https://www.elasticpath.com/
- Настроить валюту в магазине(установить 'RUB')
- Создать flow для хранения точки доставки со slug'ом `customer_address` и полями `lat`, `lon` и `user_id`
- Создать ключ доступа и получить "API Base URL" в разделе "Application Keys"
- Создать базу данных Redis и получить её адрес
- Создать бота в телеграм и получить токен
- Подключить платежи к боту
- Получить ключ геокодера яндекс
- Создать файл `.env` в папке с проектом и заполнить его следующими данными:
```commandline
MOLTIN_BASE_URL=Ваш API Base URL
MOLTIN_CLIENT_SECRET=Ваш ключ доступа
MOLTIN_CLIENT_ID=ваш ID moltin
TG_TOKEN=токен бота в телеграм
REDIS_PASSWORD=пароль базы данных 
REDIS_HOST=адрез базы данных
REDIS_PORT=порт базы данных
REDIS_USERNAME=имя пользователя от базы данных(по стандарту default)
GEOCODER_API_KEY=ключ геокодера
PAYMENT_TOKEN=токен оплаты в телеграм
```
- [Python 3.9+](https://www.python.org/downloads/) должен быть установлен
- Установить зависимости командой:
```commandline
pip install -r requirements.txt
```

## Использование
Для загрузки тестовых данных и автоматического создания flows в moltin запустите скрипт `load_menu_addresses.py`
Например:
```commandline
python load_menu_addresses.py --load_menu menu.json --load_addresses addresses.json --create_pizzeria_flow
```

Запустить бота можно командой
```
python tg-bot.py
```
После чего бот в телеграм станет активен. Для начала общения с ним используйте команду `/start`




