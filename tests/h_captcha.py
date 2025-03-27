import time
import requests
import os
import re
from playwright.sync_api import Page


class HCaptchaSolver:
    API_KEY = os.getenv('H_CAPTCHA_API')

    def __init__(self, page: Page, page_url: str):
        self.page = page
        self.page_url = page_url

    def get_sitekey(self):
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

            # Дополнительный метод: поиск в атрибутах data-sitekey
            elements = self.page.locator("[data-sitekey]")
            if elements.count() > 0:
                sitekey = elements.first.get_attribute("data-sitekey")
                if sitekey:
                    print(f"Найден sitekey в атрибуте data-sitekey: {sitekey}")
                    return sitekey

            print("Sitekey не найден.")
            return None
        except Exception as e:
            print("Ошибка при поиске sitekey:", e)
            return None

    def solve_hcatcha(self, sitekey):
        url = "https://api.solvecaptcha.com/in.php"
        payload = {
            "key": self.API_KEY,
            "method": "hcaptcha",
            "sitekey": sitekey,
            "pageurl": self.page_url,
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
        check_url = f"https://api.solvecaptcha.com/res.php?key={self.API_KEY}&action=get&id={captcha_id}&json=1"
        for _ in range(30):
            time.sleep(10)
            response = requests.get(check_url)
            result = response.json()

            if result.get("status") == 1:
                print("Капча решена")
                # Возвращаем токен и useragent для дальнейшего использования
                return {
                    "token": result["request"],
                    "useragent": result.get("useragent")
                }

            print("Ожидаем решение...")

        print("Ошибка: Капча не решена за отведённое время.")
        return None

    def submit_hcaptcha_solution(self):
        sitekey = self.get_sitekey()
        if not sitekey:
            print("Ошибка: Не найден sitekey.")
            return False

        print(f"Найден sitekey: {sitekey}")
        solution = self.solve_hcaptcha(sitekey)
        if not solution:
            print("Ошибка: Не удалось решить капчу.")
            return False

        token = solution["token"]
        useragent = solution.get("useragent")

        print(token)

        # Устанавливаем User-Agent, если он был возвращен
        if useragent:
            print(f"API вернул User-Agent: {useragent}")
            try:
                # Устанавливаем заголовки для страницы
                self.page.evaluate(f"""
                    () => {{
                        // Пытаемся установить заголовок User-Agent через JavaScript
                        try {{
                            Object.defineProperty(navigator, 'userAgent', {{
                                get: function() {{ return '{useragent}'; }}
                            }});
                            console.log("User-Agent установлен через JavaScript:", navigator.userAgent);
                        }} catch (e) {{
                            console.error("Не удалось установить User-Agent:", e);
                        }}
                    }}
                """)
            except Exception as e:
                print(f"Ошибка при установке User-Agent: {e}")

        try:
            # Улучшенный метод вставки токена с несколькими стратегиями
            result = self.page.evaluate(
                """(token) => {
                    const results = {
                        elementInserted: false,
                        callbackCalled: false,
                        eventDispatched: false,
                        methods: []
                    };

                    // Стратегия 1: Вставка токена в скрытые элементы
                    try {
                        // h-captcha-response
                        let hEl = document.querySelector("textarea[name='h-captcha-response']");
                        if (!hEl) {
                            hEl = document.createElement('textarea');
                            hEl.name = 'h-captcha-response';
                            hEl.style.display = 'none';
                            document.body.appendChild(hEl);
                        }
                        hEl.value = token;

                        // g-recaptcha-response (для совместимости)
                        let gEl = document.querySelector("textarea[name='g-recaptcha-response']");
                        if (!gEl) {
                            gEl = document.createElement('textarea');
                            gEl.name = 'g-recaptcha-response';
                            gEl.style.display = 'none';
                            document.body.appendChild(gEl);
                        }
                        gEl.value = token;

                        // Генерируем события изменения для элементов
                        for (const el of [hEl, gEl]) {
                            try {
                                // Событие изменения значения
                                const changeEvent = new Event('change', { bubbles: true });
                                el.dispatchEvent(changeEvent);

                                // Событие ввода
                                const inputEvent = new Event('input', { bubbles: true });
                                el.dispatchEvent(inputEvent);
                            } catch (e) {
                                console.error("Ошибка при генерации события:", e);
                            }
                        }

                        results.elementInserted = true;
                        results.methods.push('element_insertion');
                    } catch (e) {
                        console.error("Ошибка при вставке токена в элементы:", e);
                    }

                    // Стратегия 2: Вызов методов hCaptcha
                    try {
                        if (window.hcaptcha) {
                            // Проверяем все возможные методы hCaptcha
                            const methods = ['submit', 'execute', 'setResponse'];
                            for (const method of methods) {
                                if (typeof window.hcaptcha[method] === 'function') {
                                    try {
                                        window.hcaptcha[method](token);
                                        results.callbackCalled = true;
                                        results.methods.push('hcaptcha_' + method);
                                        console.log("Вызван метод hcaptcha." + method);
                                    } catch (e) {
                                        console.error("Ошибка при вызове hcaptcha." + method + ":", e);
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Ошибка при вызове методов hCaptcha:", e);
                    }

                    // Стратегия 3: Поиск коллбэков в атрибутах data-callback
                    try {
                        const elementsWithCallback = document.querySelectorAll("[data-callback]");
                        for (const el of elementsWithCallback) {
                            const callbackName = el.getAttribute("data-callback");
                            if (callbackName && window[callbackName]) {
                                try {
                                    window[callbackName](token);
                                    results.callbackCalled = true;
                                    results.methods.push('data_callback_' + callbackName);
                                    console.log("Вызван коллбэк из атрибута data-callback:", callbackName);
                                } catch (e) {
                                    console.error("Ошибка при вызове коллбэка " + callbackName + ":", e);
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Ошибка при поиске коллбэков в атрибутах:", e);
                    }

                    // Стратегия 4: Поиск коллбэков в конфигурации reCAPTCHA (для совместимости)
                    try {
                        if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {
                            Object.values(window.___grecaptcha_cfg.clients).forEach(client => {
                                if (client && client.callback) {
                                    try {
                                        client.callback(token);
                                        results.callbackCalled = true;
                                        results.methods.push('grecaptcha_callback');
                                        console.log("Вызван коллбэк reCAPTCHA");
                                    } catch (e) {
                                        console.error("Ошибка при вызове коллбэка reCAPTCHA:", e);
                                    }
                                }
                            });
                        }
                    } catch (e) {
                        console.error("Ошибка при поиске коллбэков reCAPTCHA:", e);
                    }

                    // Стратегия 5: Поиск функций в глобальном объекте window
                    try {
                        for (const key in window) {
                            if (typeof window[key] === 'function' && 
                                (String(key).toLowerCase().includes('captcha') || 
                                 String(key).toLowerCase().includes('token') ||
                                 String(key).toLowerCase().includes('verify'))) {
                                try {
                                    window[key](token);
                                    results.methods.push('window_function_' + key);
                                    console.log("Вызвана глобальная функция:", key);
                                } catch (e) {
                                    // Игнорируем ошибки
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Ошибка при поиске функций в window:", e);
                    }

                    // Стратегия 6: Для Stripe - поиск специфичных функций
                    try {
                        if (window.Stripe || window.stripe) {
                            const stripeObj = window.Stripe || window.stripe;
                            for (const key in stripeObj) {
                                if (typeof stripeObj[key] === 'function' && 
                                    (key.toLowerCase().includes('captcha') || 
                                     key.toLowerCase().includes('token'))) {
                                    try {
                                        stripeObj[key](token);
                                        results.methods.push('stripe_function_' + key);
                                        console.log("Вызвана функция Stripe:", key);
                                    } catch (e) {
                                        // Игнорируем ошибки
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Ошибка при работе со Stripe:", e);
                    }

                    // Стратегия 7: Генерация событий DOM
                    try {
                        // Создаем и отправляем различные события
                        const events = [
                            { name: 'hCaptchaSubmitted', detail: token },
                            { name: 'captchaVerified', detail: token },
                            { name: 'captchaSuccess', detail: token },
                            { name: 'hcaptchaVerified', detail: token },
                            { name: 'verified', detail: token },
                            { name: 'stripe:token', detail: token }
                        ];

                        for (const evt of events) {
                            try {
                                const event = new CustomEvent(evt.name, { detail: evt.detail });
                                document.dispatchEvent(event);
                                console.log("Отправлено событие:", evt.name);
                            } catch (e) {
                                console.error("Ошибка при отправке события " + evt.name + ":", e);
                            }
                        }

                        results.eventDispatched = true;
                        results.methods.push('dom_events');
                    } catch (e) {
                        console.error("Ошибка при генерации событий DOM:", e);
                    }

                    return results;
                }""",
                token
            )

            print(f"Результаты вставки токена: {result}")
            print("Токен успешно вставлен.")

        except Exception as e:
            print("Ошибка при вставке токена:", e)
            return False

        print("Токен вставлен. Ожидаем автоматическую обработку.")
        time.sleep(5)

        # Пытаемся найти и нажать кнопку отправки
        submit_selectors = [
            "form button[type='submit']",
            "form input[type='submit']",
            "button.SubmitButton",
            "button[data-testid='hosted-payment-submit-button']",
            ".submit-button",
            "button.payment-button",
            "form button:last-child"
        ]

        for selector in submit_selectors:
            try:
                submit_button = self.page.query_selector(selector)
                if submit_button:
                    print(f"Найдена кнопка отправки: {selector}")
                    submit_button.click()
                    print("Форма отправлена")
                    time.sleep(2)
                    break
            except Exception as e:
                print(f"Не удалось найти кнопку отправки {selector}:", e)

        # Проверяем, исчезла ли капча
        try:
            captcha_still_present = self.page.query_selector("iframe[src*='hcaptcha']") is not None
            if not captcha_still_present:
                print("Капча исчезла со страницы - похоже, что решение успешно принято.")
            else:
                print("Капча все еще на странице - возможно, решение не сработало.")
        except Exception as e:
            print(f"Ошибка при проверке наличия капчи: {e}")

        return True