from time import sleep
from playwright.sync_api import sync_playwright
from config.settings import Data_Setup
from src.utils import get_unverified_profile, get_credentials, get_twitter_credentials_from_json
from src.outlook_login import OutlookAutomation
from utils import get_email_password_from_json
import json
import requests
import os


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

    def login_account(self, serial_number, user_id, twitter_login, twitter_email, twitter_password):
        """Входит в твиттер аккаунт, если он не залогинен."""
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

        sleep(2)
        # Проверяем, залогинен ли аккаунт (ищем кнопку "Log in")
        if not ('i/flow/login' in twitter_page.url) and not twitter_page.locator("a[data-testid= 'loginButton']").is_visible(timeout=3000):
            print("Аккаунт уже залогинен. Вход не требуется.")
            return

        print("Аккаунт не залогинен, выполняем вход...")


        if not user_id:
            print("Ошибка: Не удалось получить user_id.")
            return

        if not twitter_password:
            print("Ошибка: Не найден пароль от Twitter в profiles.json.")
            return

        # Переход на страницу входа
        twitter_page.goto("https://x.com/i/flow/login")

        # Ввод логина
        login_input = twitter_page.locator('input[type="text"]')
        login_input.wait_for(timeout=50000)
        login_input.fill(twitter_login)
        print(f"Введен логин: {twitter_login}")

        next_button = twitter_page.locator('button div.css-146c3p1').nth(2)
        next_button.click()
        sleep(1)

        if twitter_page.locator('input[type="text"]').is_visible(timeout=3000):
            #TODO изменить локатор, тк на странице входа без подтверждения он направлен на почту
            print("Окно с подтверждением почты")
            twitter_page.locator('input[type="text"]').fill(twitter_email)
            twitter_page.locator('button[data-testid="ocfEnterTextNextButton"]').click()
            print(f"Введена почта {twitter_email}")


        password_input = twitter_page.locator('input[type="password"]')
        password_input.wait_for(timeout=50000)
        password_input.fill(twitter_password)
        print(f"Введен пароль: {twitter_password}")
        sleep(2)

        login_button = twitter_page.locator('button[data-testid="LoginForm_Login_Button"]')
        login_button.click()
        print(f"Нажата кнопка Next")
        try:
            login_button.click()
        except:
            pass

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
        sleep(3)
        twitter_page.goto("https://x.com/settings/language")

        # Определяем текущий язык
        selected_language = twitter_page.locator("select option:checked").get_attribute("value")

        if selected_language == "en":
            print("Язык уже установлен на English. Пропускаем смену языка.")
            return  # Выходим, если уже стоит английский

        print(f"Текущий язык: {selected_language}, меняем на English.")

        language_dropdown = twitter_page.locator("//select")
        language_dropdown.wait_for(timeout=50000)
        language_dropdown.select_option("en")  # Выбираем English

        save_button = twitter_page.get_by_test_id("settingsDetailSave")
        save_button.wait_for(timeout=50000)
        save_button.click()

        print("Язык изменён на английский.")

    def subscribe_twitter_blue(self):
        """Открывает страницу Twitter Blue в новой вкладке и выполняет подписку"""
        if not self.context:
            print("Ошибка: Контекст браузера отсутствует.")
            return

        print("Открываем новую вкладку для подписки Twitter Blue...")
        premium_page = self.context.new_page()
        premium_page.goto("https://x.com/i/premium_sign_up", wait_until="domcontentloaded")

        print("Переключаемся на вкладку с подпиской...")
        premium_page.bring_to_front()

        # Ждём появления и выбираем "Monthly"
        try:
            monthly_button = premium_page.locator('input[name="interval-selector"]').nth(1)
            monthly_button.wait_for(timeout=15000)
            monthly_button.click()
            print("Выбрана подписка 'Monthly'.")
        except:
            print("Ошибка: Кнопка 'Monthly' не найдена.")
            return

        # Переход к оплате
        try:
            print("Переход на страницу оплаты подписки Twitter Blue...")
            subscribe_button = premium_page.locator('[data-testid="subscribeButton"]')
            subscribe_button.wait_for(timeout=5000)
            subscribe_button.click()
            print("Успешный переход на оплату.")
        except:
            print("Ошибка: Кнопка 'Subscribe & Pay' не найдена.")

    def change_email(self, email, serial_number, user_id, twitter_login, twitter_email, twitter_password):
        """Переключается на вкладку смены языка, переходит на страницу аккаунта и вводит пароль."""
        if not self.context:
            print("Ошибка: Контекст браузера отсутствует.")
            return

        # Ищем ранее открытую вкладку со сменой языка
        language_page = None
        for page in self.pages:
            if f"x.com/{twitter_login}" in page.url:
                language_page = page
                break

        if not language_page:
            print("Ошибка: Вкладка смены языка не найдена.")
            return

        # Переключаемся на неё
        language_page.bring_to_front()
        print("Переключились на вкладку смены языка.")

        # Переход на страницу "Ваши данные Twitter"
        language_page.goto("https://x.com/settings/your_twitter_data/account", wait_until="domcontentloaded")
        print("Перешли на страницу управления аккаунтом.")

        # Ожидаем появления поля ввода пароля
        password_input = language_page.locator('input[type="password"]')
        password_input.wait_for(timeout=10000)

        if not user_id:
            print("Ошибка: Не удалось получить user_id.")
            return

        if not twitter_password:
            print("Ошибка: Не найден пароль от Twitter в profiles.json.")
            return

        # Вводим пароль
        password_input.fill(twitter_password)
        print("Пароль от Twitter введён.")

        # Нажимаем кнопку "Confirm"
        confirm_button = language_page.locator('button:has-text("Confirm")')
        confirm_button.wait_for(timeout=5000)
        sleep(2)
        confirm_button.click()
        print("Подтверждение пароля выполнено.")

        print("Переход на смену почты")
        #language_page.locator('a[data-testid="pivot"]').nth(2).click()
        language_page.goto('https://x.com/i/flow/add_email')

        language_page.locator('input[name="password"]').fill(twitter_password)
        language_page.locator('button[data-testid="LoginForm_Login_Button"]').click()
        print("Успешный переход на смену почты")


        language_page.locator('input[name="email"]').fill(email)
        language_page.locator('button[data-testid="ocfEnterEmailNextLink"]').click()
        print('Письмо отправлено на почту')

    def update_avatar(self, twitter_login):
        """Проверяет, стоит ли дефолтная аватарка, и загружает новую, если нужно."""

        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Путь к корню проекта
        AVATAR_PATH = os.path.join(BASE_DIR, "data", "avatars", "avatar.jpg")

        # Открываем вкладку Twitter и переходим в профиль
        avatar_page = None
        for page in self.pages:
            # if "x.com/settings/language" in page.url:
            if "x.com/home" in page.url:
                avatar_page = page
                break

        if not avatar_page:
            print("Ошибка: Вкладка смены языка не найдена.")
            return

        avatar_page.bring_to_front()
        print("Переключились на вкладку смены языка.")

        avatar_page.goto(f"https://x.com/{twitter_login}")
        # Проверяем, стоит ли дефолтная аватарка
        avatar = avatar_page.locator('img[alt="Opens profile photo"]')
        avatar.wait_for(timeout=50000)
        if not avatar.is_visible():
            print("Ошибка: Не найден элемент аватарки.")
            return False

        avatar_src = avatar.get_attribute("src")
        if "default_profile_200x200.png" not in avatar_src:
            print("Аватарка уже установлена, пропускаем загрузку.")
            return True

        max_retries = 3
        retries = 0
        while retries <= max_retries:
            # Открываем редактор профиля
            avatar_page.goto('https://x.com/i/flow/setup_profile')
            print("Открыто окно редактирования профиля.")

            # Ищем кнопку загрузки фото
            file_input = avatar_page.locator('input[data-testid="fileInput"]')
            file_input.wait_for(timeout=50000)  # Ждём появление элемента
            if not file_input.is_visible():
                print("Ошибка: Поле загрузки файла не найдено.")


            file_input.set_input_files(AVATAR_PATH)
            print(f"Загружается аватарка: {AVATAR_PATH}")

            # Ждём, пока Twitter обработает изображение
            sleep(3)

            # Подтверждаем изменения
            save_button = avatar_page.locator("button[data-testid='applyButton']")
            save_button.wait_for(timeout=50000)
            if save_button.is_visible():
                save_button.click()
                sleep(2)

            #Пропускаем заполнение профиля
            skip1 = avatar_page.locator("button[data-testid='ocfSelectAvatarNextButton']")
            skip2 = avatar_page.locator("button[data-testid='ocfSelectBannerSkipForNowButton']")
            skip3 = avatar_page.locator("button[data-testid='ocfEnterTextSkipForNowButton']")
            skip4 = avatar_page.locator("button[data-testid='ocfEnterTextSkipForNowButton']")
            skip5 = avatar_page.locator("button[data-testid='OCF_CallToAction_Button']")
            skip1.wait_for(timeout=50000)
            sleep(1)
            skip1.click()
            skip2.wait_for(timeout=50000)
            sleep(2)
            skip2.click()
            skip3.wait_for(timeout=50000)
            sleep(2)
            skip3.click()
            skip4.wait_for(timeout=50000)
            sleep(2)
            skip4.click()
            skip5.wait_for(timeout=50000)
            sleep(2)
            skip5.click()

            avatar_page.goto(f"https://x.com/{twitter_login}")
            # Ожидание подтверждения обновления аватарки

            sleep(5)  # Даём время на обновление
            avatar_src = avatar.get_attribute("src")
            if "default_profile_200x200.png" not in avatar_src:
                print("Аватарка успешно обновлена.")
                return True
            print(f"Аватарка не обновилась, повторяем попытку ({retries + 1}/{max_retries})...")
            #file_input.set_input_files(AVATAR_PATH)  # Повторная загрузка
            retries += 1

        print("Ошибка: Не удалось обновить аватарку.")
        return False


    def payment(self, email, password):
        if not self.context:
            print("Ошибка: Контекст браузера отсутствует.")
            return

        # Ищем ранее открытую вкладку со сменой языка
        payment_page = None
        for page in self.pages:
            if f"https://checkout.stripe.com/" in page.url:
                payment_page = page
                break

        if not payment_page:
            print("Ошибка: Вкладка смены языка не найдена.")
            return

        # Переключаемся на неё
        payment_page.bring_to_front()
        print("Переключились на оплаты.")

        #mail_input = payment_page.locator('input[id="email"]')
        cardnumber_input = payment_page.locator('input[id="cardNumber"]')
        expiry_input = payment_page.locator('input[id="cardExpiry"]')
        cvc_input = payment_page.locator('input[id="cardCvc"]')
        cardholdername_input = payment_page.locator('input[id="billingName"]')
        adress_input = payment_page.locator('input[id="billingAddressLine1"]')
        checkbox = payment_page.locator("div.CheckboxField")
        submit_button = payment_page.locator("div[class='SubmitButton-IconContainer']")

        #mail_input.fill(email)
        cardnumber_input.fill("4721070007327391")
        expiry_input.fill("1229")
        cvc_input.fill("123")
        cardholdername_input.fill("John Wick")
        adress_input.fill("645 Gladstone St, Sheridan, WY 82801")
        sleep(3)
        adress_input.press("Enter")
        sleep(1)

        if checkbox.get_attribute("class") and "--checked" in checkbox.get_attribute("class"):
            print("Чекбокс активен, отключаем...")
            checkbox.click()  # Нажимаем на него, чтобы отключить
        else:
            print("Чекбокс уже отключен.")
        sleep(3)
        submit_button.focus()  # Фокусируемся на кнопке
        payment_page.keyboard.press("Enter")  # Эмулируем нажатие Enter
        print("Оплата произведена")


if __name__ == "__main__":
    twitter_bot = TwitterAutomation()
    context, pages = twitter_bot.open_profile()

    if context:
        # Получаем все данные от профиля
        serial_number, user_id = get_unverified_profile()
        email, password = get_email_password_from_json(user_id)
        twitter_login, twitter_email, twitter_password = get_twitter_credentials_from_json(user_id)

        # Проверяем, залогинен ли аккаунт
        #twitter_bot.login_account(serial_number, user_id, twitter_login, twitter_email, twitter_password)

        #twitter_bot.set_language_to_english()  # Меняем язык в Twitter
        #twitter_bot.update_avatar(twitter_login)


        #Входим в почту, если данные есть
        # if email and password:
        #     outlook_bot = OutlookAutomation(context)
        #     outlook_bot.login_outlook(email, password)
        # else:
        #     print("Ошибка: Не найден email или пароль в profiles.json")


        #twitter_bot.subscribe_twitter_blue()
        #twitter_bot.change_email(email, serial_number, user_id, twitter_login, twitter_email, twitter_password)
        twitter_bot.payment(email, password)

    input("Нажмите Enter для выхода...")
    twitter_bot.close()


