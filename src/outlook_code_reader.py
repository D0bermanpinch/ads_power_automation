import time
import re
import traceback

from playwright.sync_api import sync_playwright
from ads_power_api import AdsPowerAPI
from src.buy_twitter_blue import TwitterAutomation
from utils import get_email_password_from_json, get_unverified_profile

class OutlookCodeReader:
    def __init__(self, context):
        self.context = context
        self.page = self.context.new_page()

    def login_outlook(self, email, password):
        """Вход в Outlook через данные из profiles.json"""
        if not self.context:
            print("Ошибка: браузерный контекст отсутствует.")
            return

        outlook_page = self.page  # Используем `self.page`

        outlook_page.goto(
            "https://login.live.com/login.srf?wa=wsignin1.0&rpsnv=171&ct=1740038207&rver=7.5.2211.0&wp=MBI_SSL&wreply=https%3a%2f%2foutlook.live.com%2fowa%2f%3fnlp%3d1%26cobrandid%3dab0455a0-8d03-46b9-b18b-df2f57b9e44c%26culture%3den-us%26country%3dus%26RpsCsrfState%3d72c5cc31-c6ce-f408-ea9f-66b9bdcae64e&id=292841&aadredir=1&whr=outlook.com&CBCXT=out&lw=1&fl=dob%2cflname%2cwld&cobrandid=ab0455a0-8d03-46b9-b18b-df2f57b9e44c",
            wait_until="domcontentloaded"
        )

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

            stay_signed_button = outlook_page.locator('button[id="acceptButton"]')
            wait_and_click(stay_signed_button, description="Оставаться залогиненым")

        except Exception:
            print("Ошибка при обработке окон:")
            print(traceback.format_exc())

        print("Почта Outlook загружена.")

    def find_twitter_code(self):
        """Сканирует почту и ищет 6-значный код от Twitter."""
        max_wait_time = 300  # 5 минут
        check_interval = 10  # Проверять каждые 10 секунд
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            print("Ищем код от Twitter в Inbox...")

            # Открываем папку Inbox и ждем загрузки
            self.page.goto("https://outlook.live.com/mail/inbox/")
            self.page.wait_for_load_state("domcontentloaded")  # Ожидание загрузки
            self.page.wait_for_timeout(3000)  # Дополнительное ожидание (3 сек)

            twitter_code = self.get_code_from_spans()
            if twitter_code:
                return twitter_code

            # Проверяем Junk Email (если нет в Inbox)
            print("Код не найден в Inbox, проверяем Junk Email...")
            self.page.goto("https://outlook.live.com/mail/junkemail/")
            self.page.wait_for_load_state("domcontentloaded")  # Ожидание загрузки
            self.page.wait_for_timeout(3000)  # Дополнительное ожидание (3 сек)

            twitter_code = self.get_code_from_spans()
            if twitter_code:
                return twitter_code

            print(f"Код не найден, ждем {check_interval} секунд...")
            time.sleep(check_interval)
            elapsed_time += check_interval

        print("Ошибка: Код от Twitter не найден.")
        return None

    def get_code_from_spans(self):
        """Ищет 6-значный код в span'ах без открытия письма."""
        spans = self.page.locator("span")
        print(f"Найдено {spans.count()} span-элементов, проверяем их содержимое...")

        for i in range(spans.count()):
            text = spans.nth(i).inner_text().strip()
            match = re.search(r"\b\d{6}\b", text)  # Ищем шестизначный код
            if match:
                print(f"Найден код: {match.group(0)}")
                return match.group(0)

        print("Код в span'ах не найден.")
        return None


def main():
    # 1. Получаем данные из AdsPower
    ads_api = AdsPowerAPI()
    serial_number, user_id = get_unverified_profile()
    if not user_id:
        print("Ошибка: Не удалось получить user_id.")
        return

    email, password = get_email_password_from_json(user_id)
    if not email or not password:
        print(f"Ошибка: Не найден email или пароль в profiles.json для user_id {user_id}.")
        return

    # 2. Открываем профиль в браузере AdsPower
    print("Открываем профиль в AdsPower...")
    twitter_bot = TwitterAutomation()
    context, pages = twitter_bot.open_profile()
    if not context:
        print("Ошибка: Не удалось открыть браузер через AdsPower.")
        return

    # 3. Читаем код из Outlook
    outlook_reader = OutlookCodeReader(context)
    #outlook_reader.login_outlook(email, password)
    twitter_code = outlook_reader.find_twitter_code()

    if twitter_code:
        print(f"Найден код от Twitter: {twitter_code}")
    else:
        print("Ошибка: Код не найден.")


if __name__ == "__main__":
    main()
