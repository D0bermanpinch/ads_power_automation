import json
import os
from playwright.sync_api import sync_playwright
from config.settings import Data_Setup
from src.utils import get_email_password_from_json, get_unverified_profile
import traceback


class OutlookAutomation:
    def __init__(self, context):
        self.context = context

    def login_outlook(self, email, password):
        """Вход в Outlook через данные из profiles.json"""
        if not self.context:
            print("Ошибка: браузерный контекст отсутствует.")
            return

        outlook_page = self.context.new_page()

        outlook_page.goto(
            "https://login.live.com/login.srf?wa=wsignin1.0&rpsnv=171&ct=1740038207&rver=7.5.2211.0&wp=MBI_SSL&wreply=https%3a%2f%2foutlook.live.com%2fowa%2f%3fnlp%3d1%26cobrandid%3dab0455a0-8d03-46b9-b18b-df2f57b9e44c%26culture%3den-us%26country%3dus%26RpsCsrfState%3d72c5cc31-c6ce-f408-ea9f-66b9bdcae64e&id=292841&aadredir=1&whr=outlook.com&CBCXT=out&lw=1&fl=dob%2cflname%2cwld&cobrandid=ab0455a0-8d03-46b9-b18b-df2f57b9e44c")
        #outlook_page.wait_for_load_state("networkidle")
        print("Ввод email...")
        email_input = outlook_page.locator('input[type="email"]')
        email_input.wait_for(timeout=100000)
        email_input.fill(email)

        outlook_page.locator('button[type="submit"]').click()

        print("Ввод пароля...")
        outlook_page.locator('input[name="passwd"]').wait_for(timeout=50000)
        outlook_page.fill('input[name="passwd"]', password)
        outlook_page.locator('button[type="submit"]').click()

        def wait_and_click(locator, timeout=5000, description=""):
            """Ждёт, пока элемент появится, и кликает, если он есть"""
            try:
                locator.wait_for(timeout=timeout)
                if locator.is_visible():
                    print(f"Нажимаем: {description}")
                    locator.click()
            except Exception:
                print(f"Окно {description} не появилось, пропускаем.")

        try:
            notification_button = outlook_page.locator('button.ms-Button--primary')
            wait_and_click(notification_button, description="Примечание об учетной записи")

            skip_button = outlook_page.locator("#iShowSkip")
            wait_and_click(skip_button, description="Пропустить защиту")
            try:
                skip_button = outlook_page.locator("#iShowSkip")
                wait_and_click(skip_button, description="Пропустить защиту")
            except:
                pass

            stay_signed_button = outlook_page.locator('button[id="acceptButton"]')
            wait_and_click(stay_signed_button, description="Оставаться залогиненым")

        except Exception:
            print("Ошибка при обработке окон:")
            print(traceback.format_exc())  # Логируем полную ошибку

        print("Предварительный вход в Outlook.")

        try:
            notification_button = outlook_page.locator('button.ms-Button--primary')
            wait_and_click(notification_button, description="Примечание об учетной записи")

            skip_button = outlook_page.locator("#iShowSkip")
            wait_and_click(skip_button, description="Пропустить защиту")

            stay_signed_button = outlook_page.locator('button[id="acceptButton"]')
            wait_and_click(stay_signed_button, description="Оставаться залогиненым")
        except:
            pass

        print("Почта Outlook загружена.")


if __name__ == "__main__":
    with sync_playwright() as p:
        user_id = get_unverified_profile()
        email, password = get_email_password_from_json(user_id)
        if not email or not password:
            print("Ошибка: Не найден email или пароль.")
            exit()

        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        outlook_bot = OutlookAutomation(context)
        outlook_bot.login_outlook(email, password)
        input("Нажмите Enter для выхода...")
        browser.close()
