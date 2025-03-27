import time
import traceback
import logging
from datetime import datetime

from playwright.sync_api import sync_playwright

from ads_power_api import AdsPowerAPI
from buy_twitter_blue import TwitterAutomation
from src.utils import get_credentials
from src.outlook_code_reader import OutlookCodeReader
from src.outlook_login import OutlookAutomation
from config.settings import Data_Setup
from utils import get_email_password_from_json, get_twitter_credentials_from_json

# Логирование ошибок
logging.basicConfig(
    filename="automation_errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def run_one_flow(playwright):
    start_time = time.time()

    try:
        # Получаем учётку
        account_data = get_credentials()
        if not account_data:
            print("Все строки в output.xlsx обработаны. Работа завершена.")
            return False

        email = account_data["Email"]
        password = account_data["Password"]
        token = account_data["Token"]
        twitter_login = account_data["Twitter Login"]
        twitter_password = account_data["Twitter Password"]
        twitter_email = account_data["Twitter Email"]

        print(f"\n=== [START] {email} ===")

        # 1. Создаём профиль
        ads_api = AdsPowerAPI()
        ads_response = ads_api.create_profile(email, password, token, twitter_login, twitter_password, twitter_email)
        if not ads_response or ads_response.get("code") != 0:
            raise Exception(f"Ошибка создания профиля для {email}")

        serial_number = ads_response["data"]["serial_number"]
        user_id = ads_response["data"]["id"]

        # 2. Работа в Twitter
        twitter_bot = TwitterAutomation(playwright)
        context, _ = twitter_bot.open_profile()

        if not context:
            raise Exception(f"Ошибка открытия профиля в AdsPower: {serial_number}")

        twitter_bot.login_account(serial_number, user_id, twitter_login, twitter_email, twitter_password)
        twitter_bot.set_language_to_english()
        twitter_bot.update_avatar(twitter_login)
        twitter_bot.update_name(twitter_login)

        # 3. Outlook
        outlook_bot = OutlookAutomation(context)
        outlook_bot.login_outlook(email, password)

        # 4. Подписка
        twitter_bot.subscribe_twitter_blue()
        twitter_bot.change_email(email, serial_number, user_id, twitter_login, twitter_email, twitter_password)

        # 5. Подтверждение
        outlook_code = OutlookCodeReader(context)
        twitter_code = outlook_code.find_twitter_code()
        twitter_bot.confirm_change_email(twitter_code)

        # 6. Оплата
        twitter_bot.payment(email, password)

        print(f"=== [DONE] {email} за {round(time.time() - start_time, 2)} сек ===\n")

        twitter_bot.close()
        return True

    except Exception:
        account_data = get_credentials()
        email = account_data["Email"]
        error_text = traceback.format_exc()
        logging.error(f"Error in {email}:{error_text}")
        print(f"[!] Ошибка на аккаунте {email}\n")
        return True  # продолжаем цикл


def main():
    with sync_playwright() as playwright:
        print("\nЗапуск полной автоматизации...\n")
        while True:
            should_continue = run_one_flow(playwright)
            if not should_continue:
                break
            time.sleep(2)
        print("\nВсе аккаунты обработаны. Скрипт завершён.")


if __name__ == "__main__":
    main()
