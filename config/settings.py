import os
from dotenv import load_dotenv

load_dotenv()

ADSP_API_URL = "http://local.adspower.net:50325/api/v1"
ADSP_API_KEY = os.getenv("ADSP_API_KEY")
PROXY_ID = os.getenv("PROXY_ID")
BROWSER_VERSION = os.getenv("BROWSER_VERSION")
OS_TYPE = os.getenv("OS_TYPE")
WEBRTC_MODE = os.getenv("WEBRTC_MODE")
