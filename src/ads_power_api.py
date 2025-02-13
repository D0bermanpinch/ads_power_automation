import requests
import json
from config.settings import Data_Setup
from src.utils import get_next_account


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

    def get_profiles(self):
        url = f"{self.base_url}/user/list"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        return response.json()

    def create_profile(self):
        account = get_next_account()
        if not account:
            print("Нет доступных аккаунтов.")
            return None

        email, password, token = account["Email"], account["Password"], account["Token"]

        url = f"{self.base_url}/user/create"
        data = {
            "apiKey": self.api_key,
            "group_id": self.group_id,
            "domain_name": "x.com",
            "user_proxy_config": {
                "proxy_type": "http",
                "proxy_host": "5.161.22.120",
                "proxy_port": 13757,
                "proxy_user": self.proxy_user,
                "proxy_password": self.proxy_password,
                "proxy_url": self.proxy_url,
                "proxy_soft": "other"
            },
            "fingerprint_config": {
                "browser": self.browser_version,
                "ua": self.os_type,  # Пробуем передать OS
                "webrtc": self.webrtc_mode,
                "canvas": 0,  # Выключаем Canvas
                "webgl_image": 0  # Выключаем WebGL Image
            },
            "cookie": json.dumps([
                {
                    "domain": ".twitter.com",
                    "httpOnly": False,
                    "path": "/",
                    "secure": False,
                    "expirationDate": 1739009685,
                    "name": "auth_token",
                    "value": token
                }]
            )
        }

        response = requests.post(url, json=data)
        print(response.json())  # Логируем ответ API
        return response.json()


if __name__ == "__main__":
    api = AdsPowerAPI()
    new_profile = api.create_profile()
