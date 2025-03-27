import time
import os
import re
import base64
import requests
from time import sleep
from playwright.sync_api import Page
from src.utils import mark_card_declined, mark_payment_failed, mark_payment_success


class HCaptchaSolver:
    API_KEY = os.getenv('H_CAPTCHA_API')
    SOLVE_CAPTCHA_IN_URL = "https://api.solvecaptcha.com/in.php"
    SOLVE_CAPTCHA_RES_URL = "https://api.solvecaptcha.com/res.php"

    def __init__(self, page: Page, page_url: str):
        self.page = page
        self.page_url = page_url

    def get_sitekey(self):
        sleep(3)
        # Ищем sitekey в iframe src или data-sitekey
        try:
            frames = self.page.locator("iframe")
            count = frames.count()
            for i in range(count):
                src = frames.nth(i).get_attribute("src")
                if src and "sitekey=" in src:
                    match = re.search(r"sitekey=([a-z0-9\-]+)", src)
                    if match:
                        print(f"Найден sitekey в iframe: {match.group(1)}")
                        return match.group(1)

            elements = self.page.locator("[data-sitekey]")
            if elements.count() > 0:
                sitekey = elements.first.get_attribute("data-sitekey")
                if sitekey:
                    print(f"Найден sitekey в data-sitekey: {sitekey}")
                    return sitekey

            return None
        except Exception as e:
            print("Ошибка при поиске sitekey:", e)
            return None

    def send_screenshot_for_clickcaptcha(self, image_path: str, instructions: str = "PLEASE CLICK an animal that doesn't have a mate in the photo") -> str:
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        data = {
            "key": self.API_KEY,
            "method": "base64",
            "coordinatescaptcha": "1",
            "max_clicks": "1",
            "body": b64_data,
            "textinstructions": instructions,  # текстовые инструкции, если нужно
            "json": "1"
        }

        resp = requests.post(self.SOLVE_CAPTCHA_IN_URL, data=data)
        resp_json = resp.json()
        if resp_json.get("status") != 1:
            print("Ошибка при отправке капчи:", resp_json)
            return None

        cap_id = resp_json["request"]
        print(f"Капча отправлена, ID: {cap_id}")
        return cap_id

    def get_clickcaptcha_result(self, cap_id: str, max_retries: int = 30, delay: int = 5) -> str:
        for _ in range(max_retries):
            time.sleep(delay)
            params = {
                "key": self.API_KEY,
                "action": "get",
                "id": cap_id,
                "json": "1"
            }
            resp = requests.get(self.SOLVE_CAPTCHA_RES_URL, params=params)
            rj = resp.json()

            if rj.get("status") == 1:
                return rj["request"]  # строка вида "coordinate:x=39,y=59;x=252,y=72"
            elif rj["request"] == "CAPCHA_NOT_READY":
                print("Ожидаем решение капчи...")
                continue
            else:
                print("Ошибка при получении результата:", rj)
                return None

        print("Капча не решена за отведённое время.")
        return None

    def parse_coordinates(self, raw_coords):
        if isinstance(raw_coords, list):
            # Уже список словарей: [{"x":"905","y":"413"} ...]
            result = []
            for item in raw_coords:
                x_val = int(item["x"])
                y_val = int(item["y"])
                result.append((x_val, y_val))
            return result
        elif isinstance(raw_coords, str):
            # Старый текстовый формат: "coordinate:x=39,y=59;x=252,y=72"
            # Или "x=39,y=59;x=252,y=72"
            parts = raw_coords.split(";")
            coords = []
            for p in parts:
                p = p.replace("coordinate:", "").strip()
                xy = p.split(",")
                x_val = int(xy[0].split("=")[1])
                y_val = int(xy[1].split("=")[1])
                coords.append((x_val, y_val))
            return coords
        else:
            print("Неизвестный формат координат:", raw_coords)
            return []

    def submit_hcaptcha_solution(self, email):
        sleep(5)
        checkbox_x, checkbox_y = 840, 430
        print("Пытаемся нажать на чекбокс...")
        self.page.mouse.click(checkbox_x, checkbox_y)


        sleep(4)

        loop_count = 0
        max_loops = 8
        while loop_count < max_loops:

            error_locator = self.page.locator('div.ConfirmPaymentButton-Error.Notice.Notice--red')
            if error_locator.is_visible():
                print("Обнаружена ошибка оплаты. Прерываем цикл.")
                mark_payment_failed(email)
                return False

            #if self.page.url.startswith("https://x.com/i/premium_sign_up/successful"):
            if f"x.com/i/premium_sign_up/successful" in self.page.url:
                print("Переход на страницу успешной подписки. Прерываем цикл.")
                mark_payment_success(email)
                return True

            loop_count += 1
            sk = self.get_sitekey()
            if not sk:
                print("hCaptcha не обнаружена, выходим из цикла.")
                return True

            captcha_steps = 0
            while captcha_steps <=2:
                # 1) Скриншот
                sleep(2)
                timestamp = int(time.time())
                screenshot_path = f"captchascreenshoots/hcaptcha_{timestamp}.png"
                self.page.screenshot(path=screenshot_path)
                print(f"[Попытка {loop_count}] Скриншот: {screenshot_path}")

                # 2) Отправляем в SolveCaptcha
                cap_id = self.send_screenshot_for_clickcaptcha(screenshot_path, instructions="PLEASE CLICK an animal that doesn't have a mate in the photo")
                if not cap_id:
                    print("Ошибка отправки капчи.")
                    continue

                # 3) Ждём ответа
                raw_coords = self.get_clickcaptcha_result(cap_id)
                if not raw_coords:
                    print("Нет ответа с координатами, повторяем.")
                    continue

                print("Ответ от SolveCaptcha:", raw_coords)
                coords = self.parse_coordinates(raw_coords)
                if not coords:
                    print("Ошибка: координаты не распознаны.")
                    continue

                # 4) Кликаем
                for (cx, cy) in coords:
                    print(f"Кликаем по ({cx}, {cy})")
                    self.page.mouse.click(cx, cy)
                    sleep(4)

                # 5) Нажимаем Next
                next_x, next_y = 1322, 649
                print("Нажимаем Next...")
                self.page.mouse.click(next_x, next_y)
                sleep(2)

            # # Проверяем, исчезла ли капча
            # if not self.get_sitekey():
            #     print("Капча исчезла после нажатия Next! Успех.")
            #     return True
            #
            # print("hCaptcha ещё здесь, повторяем...\n")

        print("Превышен лимит попыток, капча не снята.")
        return False
