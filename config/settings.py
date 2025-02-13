import os
from dotenv import load_dotenv

load_dotenv()

class Data_Setup:

    ADSP_API_URL = "http://local.adspower.net:50325/api/v1"
    ADSP_API_KEY = os.getenv("ADSP_API_KEY")
    PROXY_ID = os.getenv("PROXY_ID")
    PROXY_USER = os.getenv("PROXY_USER")
    PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
    PROXY_URL = os.getenv("PROXY_URL")
    BROWSER_VERSION = os.getenv("BROWSER_VERSION")
    OS_TYPE = os.getenv("OS_TYPE")
    WEBRTC_MODE = os.getenv("WEBRTC_MODE")
    GROUP_ID = os.getenv("GROUP_ID")
