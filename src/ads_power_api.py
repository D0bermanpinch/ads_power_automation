import requests
import json
import os
from config.settings import ADSP_API_URL, ADSP_API_KEY, PROXY_ID, BROWSER_VERSION, OS_TYPE, WEBRTC_MODE
from src.utils import get_next_account

class AdsPowerAPI:
    def __init__(self):
        self.base_url = ADSP_API_URL
        self.api_key = ADSP_API_KEY

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

        cookies = json.dumps([{
            "domain": ".twitter.com",
            "httpOnly": False,
            "path": "/",
            "secure": False,
            "expirationDate": 1739009685,
            "name": "auth_token",
            "value": token
        }])

        url = f"{self.base_url}/user/create"
        data = {
            "apiKey": self.api_key,
            "group_id": "Max",
            "domain_name": "x.com",
            "proxy_id": PROXY_ID,
            "fingerprint_config": {
                "browser": BROWSER_VERSION,
                "os": OS_TYPE,
                "webrtc": WEBRTC_MODE
            },
            "cookies": cookies
        }
        response = requests.post(url, json=data)
        return response.json()

if __name__ == "__main__":
    api = AdsPowerAPI()
    new_profile = api.create_profile()
    print(new_profile)
