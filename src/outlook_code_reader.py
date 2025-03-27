import time
import re
from time import sleep


class OutlookCodeReader:
    def __init__(self, context):
        self.context = context
        self.page = self.context.new_page()

    def find_twitter_code(self):
        """Сканирует почту и ищет 6-значный код от Twitter."""
        max_wait_time = 300  # 5 минут
        check_interval = 10  # Проверять каждые 10 секунд
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            print("Ищем код от Twitter в Inbox...")
            sleep(2)
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
        try:
            self.page.locator("span").first.wait_for(timeout=5000)  # Убедимся, что хотя бы один span есть
        except Exception:
            print("Span-элементы не появились.")
            return None

        try:
            # Получаем ВСЕ тексты за раз, чтобы не дёргать DOM по одному
            texts = self.page.locator("span").all_inner_texts()
            print(f"Получено {len(texts)} span-элементов, проверяем их содержимое...")

            for text in texts:
                text = text.strip()
                match = re.search(r"\b\d{6}\b", text)
                if match:
                    print(f"Найден код: {match.group(0)}")
                    return match.group(0)

        except Exception as e:
            print("Ошибка при получении текста из span-элементов:")
            print(e)

        print("Код в span'ах не найден.")
        return None

