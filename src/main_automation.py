import time
from ads_power_api import AdsPowerAPI
from buy_twitter_blue import TwitterAutomation
from outlook_login import OutlookAutomation
from src.utils import get_email_password_from_xlsx


def main():
    start_time = time.time()  # Начало всего процесса

    # 1. Создание профиля в AdsPower
    ads_start = time.time()
    ads_api = AdsPowerAPI()
    new_profile = ads_api.create_profile()
    ads_end = time.time()

    if not new_profile or new_profile.get("code") != 0:
        print("Ошибка при создании профиля.")
        return

    serial_number = new_profile["data"]["serial_number"]
    user_id = new_profile["data"]["id"]
    print(f"✅ Профиль создан за {ads_end - ads_start:.2f} секунд.")

    # 2. Открытие Twitter-профиля и смена языка
    twitter_start = time.time()
    twitter_bot = TwitterAutomation()
    context, pages = twitter_bot.open_profile()

    if context:
        twitter_bot.set_language_to_english()  # Меняем язык в Twitter
        print("✅ Язык изменён на английский.")

    twitter_end = time.time()
    print(f"✅ Twitter открыт и язык изменён за {twitter_end - twitter_start:.2f} секунд.")

    # 3. Вход в Outlook
    outlook_start = time.time()
    email, password = get_email_password_from_xlsx()
    if email and password:
        outlook_bot = OutlookAutomation(context)
        outlook_bot.login_outlook(email, password)
    else:
        print("Ошибка: Не найден email или пароль в output.xlsx")
    outlook_end = time.time()
    print(f"✅ Вход в Outlook выполнен за {outlook_end - outlook_start:.2f} секунд.")

    # 4. Открываем подписку Twitter Blue в новой вкладке
    twitter_bot.subscribe_twitter_blue()
    print("✅ Открыта подписка Twitter Blue в новой вкладке.")

    total_time = time.time() - start_time
    print(f"⏳ Весь процесс занял {total_time:.2f} секунд.")

    input("Нажмите Enter для выхода...")
    twitter_bot.close()


if __name__ == "__main__":
    main()
