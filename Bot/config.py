import os
from typing import Final

# Токен читается из переменной окружения. В коде его больше нет.
BOT_TOKEN: Final = os.getenv("BOT_TOKEN", "")

ASICMINERVALUE_URL: Final = "https://www.asicminervalue.com/miners"
WHATTOMINE_URL: Final = "https://whattomine.com/asics"
DEFAULT_KWH: Final = 0.10
REFRESH_HOURS: Final = 12
SERVICE_BASE_URL: Final = os.getenv("SERVICE_BASE_URL", "http://127.0.0.1:8000")
