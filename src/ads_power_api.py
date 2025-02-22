import requests
import json
import os
from datetime import datetime, timezone
from config.settings import Data_Setup
from src.utils import get_credentials

PROFILES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "profiles.json")


def save_profile(email, password, serial_number, user_id, token, twitter_login, twitter_password, twitter_email):
    """Сохраняет профиль в profiles.json"""
    profile_data = {
        "email": email,
        "password": password,
        "twitter_login": twitter_login,
        "twitter_password": twitter_password,
        "twitter_email": twitter_email,
        "user_id": user_id,  # Генерировать или получать из другого источника
        "serial_number": serial_number,  # Генерировать или получать из другого источника
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bought": False
    }

    # Проверка, существует ли файл профилей
    if os.path.exists(PROFILES_PATH):
        try:
            with open(PROFILES_PATH, "r", encoding="utf-8") as f:
                profiles = json.load(f)
        except json.JSONDecodeError:
            profiles = []  # Если файл пустой или битый, создаём пустой список
    else:
        profiles = []

    profiles.append(profile_data)

    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)


class AdsPowerAPI:
    def __init__(self):
        self.base_url = Data_Setup.ADSP_API_URL
        self.api_key = Data_Setup.ADSP_API_KEY
        self.proxy_id = Data_Setup.PROXY_ID
        self.browser_version = Data_Setup.BROWSER_VERSION
        self.os_type = Data_Setup.OS_TYPE
        self.webrtc_mode = Data_Setup.WEBRTC_MODE
        self.group_id = Data_Setup.GROUP_ID
        self.proxy_user = Data_Setup.PROXY_USER
        self.proxy_password = Data_Setup.PROXY_PASSWORD
        self.proxy_url = Data_Setup.PROXY_URL
        self.proxy_type = Data_Setup.PROXY_TYPE
        self.proxy_host = Data_Setup.PROXY_HOST
        self.proxy_port = Data_Setup.PROXY_PORT

    def create_profile(self, email, password, token, twitter_login, twitter_password, twitter_email):
        """Создает профиль и сохраняет данные в profiles.json"""
        # Формируем данные для API запроса
        url = f"{self.base_url}/user/create"
        data = {
            "apiKey": self.api_key,
            "group_id": self.group_id,
            "domain_name": "x.com",
            "user_proxy_config": {
                "proxy_type": self.proxy_type,
                "proxy_host": self.proxy_host,
                "proxy_port": self.proxy_port,
                "proxy_user": self.proxy_user,
                "proxy_password": self.proxy_password,
                "proxy_url": self.proxy_url,
                "proxy_soft": "other"
            },
            "fingerprint_config": {
                "browser": self.browser_version,
                "ua": self.os_type,
                "webrtc": self.webrtc_mode,
                "canvas": 0,
                "webgl_image": 0
            },
            "cookie": json.dumps([{
                "domain": ".twitter.com",
                "httpOnly": False,
                "path": "/",
                "secure": False,
                "expirationDate": 1739009685,
                "name": "auth_token",
                "value": token
            }])
        }

        response = requests.post(url, json=data)
        print(response)

        try:
            response_json = response.json()  # Преобразуем response в JSON
        except json.JSONDecodeError:
            print("Ошибка: сервер вернул некорректный JSON.")
            return None

        if response_json.get("code") == 0:
            serial_number = response_json["data"]["serial_number"]
            user_id = response_json["data"]["id"]
            save_profile(email, password, serial_number, user_id, token, twitter_login, twitter_password, twitter_email)

        print(response.json())  # Логируем ответ API
        return response_json


if __name__ == "__main__":
    api = AdsPowerAPI()
    account_data = get_credentials()  # Получаем данные из utils.py

    if account_data:  # Если данные получены, передаем их в create_profile
        # Извлекаем данные для передачи в create_profile
        email = account_data["Email"]
        password = account_data["Password"]
        token = account_data["Token"]
        twitter_login = account_data["Twitter Login"]
        twitter_password = account_data["Twitter Password"]
        twitter_email = account_data["Twitter Email"]

        # Вызываем create_profile с полученными данными
        api.create_profile(email, password, token, twitter_login, twitter_password, twitter_email)
    else:
        print("Ошибка: Не удалось получить данные для аккаунта.")
