import httpx
from typing import Dict, List
from .schemas import AlgorithmOut
from .config import settings
from .cache import ttl_cache


async def fetch_nicehash_algorithms() -> List[AlgorithmOut]:
    cache_key = "nh_algos_raw"
    cached = ttl_cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{settings.NH_BASE}/main/api/v2/public/simplemultialgo/info"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    out: List[AlgorithmOut] = []
    for item in data.get("miningAlgorithms", []):
        algo_id = (item.get("algorithm", {}) or {}).get("enumName") or item.get("enumName") or item.get("name")
        name = item.get("displayName") or algo_id
        unit = item.get("speedText") or "H/s"
        paying = item.get("paying") or 0.0
        out.append(
            AlgorithmOut(
                id=str(algo_id),
                name=str(name),
                unit=str(unit).replace("/s", "").upper(),
                paying_btc_per_unit_per_day=float(paying),
            )
        )

    ttl_cache.set(cache_key, out, ttl_seconds=settings.NH_TTL_SECONDS)
    return out


async def fetch_btc_prices() -> Dict[str, float]:
    cache_key = "btc_prices"
    cached = ttl_cache.get(cache_key)
    if cached is not None:
        return cached

    vs = ["rub", "usd", "eur", "czk"]
    url = f"{settings.CG_BASE}/api/v3/simple/price?ids=bitcoin&vs_currencies={','.join(vs)}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    btc = data.get("bitcoin", {})
    out = {
        "RUB": float(btc.get("rub", 0.0)),
        "USD": float(btc.get("usd", 0.0)),
        "EUR": float(btc.get("eur", 0.0)),
        "CZK": float(btc.get("czk", 0.0)),
    }
    ttl_cache.set(cache_key, out, ttl_seconds=settings.PRICES_TTL_SECONDS)
    return out





