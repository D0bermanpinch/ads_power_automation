import time
from ads_power_api import AdsPowerAPI
from buy_twitter_blue import TwitterAutomation
from src.outlook_login import OutlookAutomation
from utils import get_credentials, get_email_password_from_json


def main():
    start_time = time.time()  # Начало всего процесса

    # 1. Создание профиля в AdsPower
    ads_start = time.time()
    ads_api = AdsPowerAPI()
    account_data = get_credentials()  # Получаем данные из output.xlsx

    if not account_data:  # Проверяем, получены ли данные
        print("Ошибка: Не удалось получить учетные данные из output.xlsx.")
        return

    # Извлекаем данные для передачи в create_profile
    email = account_data["Email"]
    password = account_data["Password"]
    token = account_data["Token"]
    twitter_login = account_data["Twitter Login"]
    twitter_password = account_data["Twitter Password"]
    twitter_email = account_data["Twitter Email"]

    new_profile = ads_api.create_profile(email, password, token, twitter_login, twitter_password, twitter_email)
    ads_end = time.time()

    if not new_profile or new_profile.get("code") != 0:
        print("Ошибка при создании профиля.")
        return

    serial_number = new_profile["data"]["serial_number"]
    user_id = new_profile["data"]["id"]
    print(f"Профиль создан за {ads_end - ads_start:.2f} секунд (user_id: {user_id})")

    # 2. Открытие Twitter-профиля и выполнение всех операций
    twitter_start = time.time()
    twitter_bot = TwitterAutomation()
    context, pages = twitter_bot.open_profile()

    if context:
        # Проверяем, залогинен ли аккаунт, если нет - входим
        twitter_bot.login_account()

        # Смена языка на английский
        twitter_bot.set_language_to_english()
        print("Язык изменён на английский.")

        # Открытие подписки Twitter Blue
        twitter_bot.subscribe_twitter_blue()
        print("Переключились на вкладку подписки Twitter Blue.")

        # Смена почты
        twitter_bot.change_email()
        print("Начат процесс смены почты.")

    twitter_end = time.time()
    print(f"Все операции в Twitter выполнены за {twitter_end - twitter_start:.2f} секунд.")

    # 3. Вход в Outlook для подтверждения кода
    outlook_start = time.time()
    email, password = get_email_password_from_json(user_id)

    if email and password:
        # Открываем новую вкладку для Outlook
        outlook_page = context.new_page()
        outlook_bot = OutlookAutomation(outlook_page)

        # Выполняем вход
        outlook_bot.login_outlook(email, password)
    else:
        print(f"Ошибка: Не найден email или пароль в profiles.json для user_id {user_id}.")

    outlook_end = time.time()
    print(f"Вход в Outlook выполнен за {outlook_end - outlook_start:.2f} секунд.")

    total_time = time.time() - start_time
    print(f"Весь процесс занял {total_time:.2f} секунд.")

    input("Нажмите Enter для выхода...")
    twitter_bot.close()


if __name__ == "__main__":
    main()
