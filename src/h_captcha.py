import time
import traceback
import requests
from playwright.sync_api import sync_playwright

API_KEY = "be29b5ba4d24ac454f037e8359c39a69"  # ключ SolveCaptcha
TARGET_URL = "https://democaptcha.com/demo-form-eng/hcaptcha.html"  # Страница с hCaptcha


def solve_hcaptcha(sitekey, pageurl):
    """Отправляет sitekey в API и получает решение hCaptcha"""
    url = "https://api.solvecaptcha.com/in.php"
    payload = {
        "key": API_KEY,
        "method": "hcaptcha",
        "sitekey": sitekey,
        "pageurl": pageurl,
        "json": "1"
    }

    response = requests.post(url, data=payload)
    result = response.json()

    if result.get("status") != 1:
        print("Ошибка при отправке капчи:", result)
        return None

    captcha_id = result["request"]
    print(f"Капча отправлена. ID: {captcha_id}")

    # Ожидание решения
    check_url = f"https://api.solvecaptcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}&json=1"
    for _ in range(30):  # Ожидать максимум 150 секунд (30x5)
        time.sleep(5)
        response = requests.get(check_url)
        result = response.json()

        if result.get("status") == 1:
            print("Капча решена:", result["request"])
            return result["request"]

        print("Ожидаем решение...")

    print("Ошибка: Капча не решена за отведённое время.")
    return None


def get_sitekey(page):
    """Находит sitekey на странице"""
    try:
        sitekey_element = page.locator('div[class*="h-captcha"]').first
        sitekey = sitekey_element.get_attribute("data-sitekey")
        return sitekey
    except:
        print("Ошибка: sitekey не найден.")
        return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Меняй на True для фонового режима
        page = browser.new_page()

        # 1. Открываем страницу с hCaptcha
        print("Открываем страницу:", TARGET_URL)
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")


        # 3. Извлекаем sitekey
        sitekey = get_sitekey(page)
        if not sitekey:
            print("Ошибка: Не найден sitekey.")
            browser.close()
            return

        print(f"Найден sitekey: {sitekey}")

        # 4. Решаем капчу
        captcha_solution = solve_hcaptcha(sitekey, TARGET_URL)
        if not captcha_solution:
            print("Ошибка: Не удалось решить капчу.")
            traceback.print_exc()
            browser.close()
            return

        # 5. Вставляем решение в поле ответа капчи
        print("Вставляем капчу...")
        page.evaluate(f'document.querySelector("textarea[name=\'h-captcha-response\']").value = "{captcha_solution}";')
        submit_button = page.locator('input[type="submit"].btn.btn-install')

        if submit_button.is_enabled():
            submit_button.click()
        else:
            print("Ошибка: Кнопка недоступна для нажатия.")

        time.sleep(3)  # Даем время на обработку
        browser.close()
        print("Готово.")


if __name__ == "__main__":
    main()
