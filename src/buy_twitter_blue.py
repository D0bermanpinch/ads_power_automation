import requests
from playwright.sync_api import sync_playwright
from config.settings import Data_Setup
from src.utils import get_unverified_profile
import json


class TwitterAutomation:
    def __init__(self):
        self.base_url = Data_Setup.ADSP_API_URL
        self.api_key = Data_Setup.ADSP_API_KEY
        self.playwright = sync_playwright().start()  # Запускаем Playwright
        self.browser = None
        self.context = None
        self.pages = []

    def start_browser(self, serial_number, user_id):
        """Открывает профиль в AdsPower и возвращает WebSocket URL"""
        url = f"{self.base_url}/browser/start"  # Исправленный URL
        params = {"apiKey": self.api_key,"user_id": user_id, "serial_number": serial_number}

        print(f"Запрос к AdsPower: {url}, параметры: {params}")  # Логируем запрос

        response = requests.get(url, params=params)

        if not response.text.strip():  # Если API вернул пустую строку
            print("Ошибка: пустой ответ от AdsPower API")
            return None

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            print(f"Ошибка: некорректный JSON от AdsPower API. Ответ сервера: {response.text}")
            return None

        if response_json.get("code") == 0:
            return response_json["data"]["ws"]["selenium"]
        else:
            print(f"Ошибка запуска браузера: {response_json['msg']}")
            return None

    def open_profile(self):
        """Открывает AdsPower браузер и подключается Playwright"""
        serial_number, user_id = get_unverified_profile()
        if not serial_number or not user_id:
            print("Нет профилей для обработки.")
            return None

        ws_url = self.start_browser(serial_number, user_id)
        if ws_url and not ws_url.startswith("http"):
            ws_url = f"http://{ws_url}"

        print(f"WebSocket URL: {ws_url}")  # Проверяем, какой URL вернул API
        if not ws_url:
            return None

        self.browser = self.playwright.chromium.connect_over_cdp(ws_url)
        self.context = self.browser.contexts[0]
        self.pages = self.context.pages  # Сохраняем страницы в self.pages

        print(f"Открыто вкладок: {len(self.pages)}")
        for i, page in enumerate(self.pages):
            print(f"[{i}] {page.url}")

        # Автоматически переключаемся на вкладку Twitter, если она есть
        for page in self.pages:
            if "x.com" in page.url or "twitter.com" in page.url:
                page.bring_to_front()
                print(f"Активирована вкладка: {page.url}")
                break

        return self.context, self.pages

    def close(self):
        """Закрывает браузер и Playwright"""
        if self.browser:
            self.browser.close()
        self.playwright.stop()

    def set_language_to_english(self):
        """Меняет язык Twitter-профиля на английский"""
        if not self.pages:
            print("Нет доступных вкладок.")
            return

        twitter_page = None

        # Ищем вкладку с Twitter
        for page in self.pages:
            if "x.com" in page.url or "twitter.com" in page.url:
                twitter_page = page
                break

        if not twitter_page:
            print("Вкладка Twitter не найдена.")
            return

        print("Переход на страницу смены языка...")
        twitter_page.goto("https://x.com/settings/language")

        # Определяем текущий язык
        selected_language = twitter_page.locator("select option:checked").get_attribute("value")

        if selected_language == "en":
            print("Язык уже установлен на English. Пропускаем смену языка.")
            return  # Выходим, если уже стоит английский

        print(f"Текущий язык: {selected_language}, меняем на English.")

        # pivot = twitter_page.locator('[data-testid="pivot"]').nth(3)
        # #pivot.wait_for(timeout=50000)
        # pivot.click()

        language_dropdown = twitter_page.locator("//select")
        language_dropdown.wait_for(timeout=5000)
        language_dropdown.select_option("en")  # Выбираем English

        save_button = twitter_page.get_by_test_id("settingsDetailSave")
        save_button.wait_for(timeout=5000)
        save_button.click()

        print("Язык изменён на английский.")


if __name__ == "__main__":
    twitter_bot = TwitterAutomation()
    context, pages = twitter_bot.open_profile()
    twitter_bot.set_language_to_english()

    # Теперь context и pages доступны даже после выхода из функции
    input("Нажмите Enter для выхода...")
    twitter_bot.close()
