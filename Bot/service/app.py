import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from .schemas import (
    AlgorithmOut,
    CalculateRequest,
    CalculateResponse,
    PeriodsOut,
    DeviceOut,
)
from .clients import fetch_nicehash_algorithms, fetch_btc_prices
from .config import settings
from .cache import ttl_cache

app = FastAPI(title="Mining Profitability Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/algorithms", response_model=list[AlgorithmOut])
async def get_algorithms():
    try:
        cache_key = "nh_algorithms"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return cached

        algos = await fetch_nicehash_algorithms()
        ttl_cache.set(cache_key, algos, ttl_seconds=settings.NH_TTL_SECONDS)
        return algos
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Algorithms unavailable: {e}")


@app.post("/calculate", response_model=CalculateResponse)
async def calculate(req: CalculateRequest):
    periods = req.periods or ["1h", "24h", "168h", "720h"]

    algos = await get_algorithms()  # cached
    algo = next((a for a in algos if a.id.upper() == req.algoId.upper()), None)
    if not algo:
        raise HTTPException(status_code=400, detail=f"Unknown algoId={req.algoId}")

    unit_factors = {
        "H": 1.0,
        "KH": 1e3,
        "MH": 1e6,
        "GH": 1e9,
        "TH": 1e12,
        "PH": 1e15,
        "EH": 1e18,
    }
    user_unit = req.hashrate.unit.upper()
    base_unit = algo.unit.upper()
    if user_unit not in unit_factors or base_unit not in unit_factors:
        raise HTTPException(status_code=400, detail="Unsupported unit")

    value_hs = req.hashrate.value * unit_factors[user_unit]
    base_value = value_hs / unit_factors[base_unit]

    revenue_btc_day = algo.paying_btc_per_unit_per_day * base_value

    prices = await fetch_btc_prices()
    fiat = req.fiat.upper()
    btc_price = prices.get(fiat)
    if not btc_price:
        raise HTTPException(status_code=400, detail=f"Unsupported fiat {fiat}")

    elect_price = req.electricity.value
    elect_ccy = req.electricity.currency.upper()
    if elect_ccy != fiat:
        if elect_ccy == "USD" and fiat in prices and "USD" in prices:
            rate = prices[fiat] / prices["USD"]
            elect_price = elect_price * rate
        elif elect_ccy == "RUB" and fiat in prices and "RUB" in prices:
            rate = prices[fiat] / prices["RUB"]
            elect_price = elect_price * rate
    elect_cost_day = (req.power_w / 1000.0) * elect_price * 24.0

    total_fee_pct = (req.fees.marketplace_pct + req.fees.pool_pct) / 100.0
    uptime_factor = max(0.0, min(1.0, req.uptime_pct / 100.0))

    revenue_fiat_day = revenue_btc_day * btc_price
    fees_fiat_day = revenue_fiat_day * total_fee_pct
    net_profit_fiat_day = (revenue_fiat_day - fees_fiat_day) * uptime_factor - elect_cost_day * uptime_factor

    def scale(x_day: float, period: str) -> float:
        return x_day / 24.0 if period == "1h" else (
            x_day if period == "24h" else (
                x_day * 7 if period == "168h" else (
                    x_day * 30 if period == "720h" else x_day
                )
            )
        )

    periods_map = {
        p: {
            "revenue_btc": scale(revenue_btc_day, p),
            "revenue_fiat": scale(revenue_fiat_day, p),
            "electricity_cost_fiat": scale(elect_cost_day, p),
            "fees_fiat": scale(fees_fiat_day, p),
            "net_profit_fiat": scale(net_profit_fiat_day, p),
        }
        for p in periods
    }

    out = CalculateResponse(
        algoId=algo.id,
        unit=algo.unit,
        btc_price={fiat: btc_price},
        periods=PeriodsOut(__root__=periods_map),
        disclaimer=f"Расчёты ориентировочные; используйте актуальные данные. Источник: NiceHash API на {datetime.utcnow().date().isoformat()}.",
    )
    return out


@app.get("/devices", response_model=list[DeviceOut])
async def get_devices():
    # Curated minimal presets; can be extended or scraped later
    return [
        DeviceOut(
            id="antminer_s21_xp_hydro",
            vendor="Bitmain",
            model="Antminer S21 XP Hydro",
            algoId="SHA256",
            nominal_hashrate_value=473,
            unit="TH",
            power_w=5676,
            price_fiat=None,
        ),
        DeviceOut(
            id="antminer_s19_pro",
            vendor="Bitmain",
            model="Antminer S19 Pro",
            algoId="SHA256",
            nominal_hashrate_value=110,
            unit="TH",
            power_w=3250,
            price_fiat=None,
        ),
        DeviceOut(
            id="iceriver_ks3",
            vendor="IceRiver",
            model="KS3",
            algoId="KHEAVYHASH",
            nominal_hashrate_value=8,
            unit="TH",
            power_w=3200,
            price_fiat=None,
        ),
        DeviceOut(
            id="goldshell_lt5",
            vendor="Goldshell",
            model="LT5",
            algoId="SCRYPT",
            nominal_hashrate_value=2.05,
            unit="GH",
            power_w=2080,
            price_fiat=None,
        ),
    ]


