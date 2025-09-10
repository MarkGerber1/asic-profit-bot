import os
from dataclasses import dataclass


@dataclass
class Settings:
    NH_BASE: str = os.getenv("NH_BASE", "https://api2.nicehash.com")
    CG_BASE: str = os.getenv("CG_BASE", "https://api.coingecko.com")
    NH_TTL_SECONDS: int = int(os.getenv("NH_TTL_SECONDS", "120"))
    PRICES_TTL_SECONDS: int = int(os.getenv("PRICES_TTL_SECONDS", "60"))


settings = Settings()





