import httpx

COIN_ID_BY_ALGO = {
    # Базовые
    "SHA-256": "bitcoin",
    "SCRYPT": "litecoin",
    "X11": "dash",
    "KHEAVYHASH": "kaspa",  # Kaspa
    "ETHASH": "ethereum-classic",  # ETC
    "EQUIHASH": "zcash",  # ZEC
    "ZKSNARK": "zcash",
    # Дополнительные ASIC-алгоритмы
    "BLAKE2S": "kadena",  # KDA
    "KADENA": "kadena",
    "BLAKE2B": "siacoin",  # SC
    "SIACOIN": "siacoin",
    "HANDSHAKE": "handshake",  # HNS
    "HNS": "handshake",
    "EAGLESONG": "nervos-network",  # CKB
    "CKB": "nervos-network",
    "BLAKE3": "alephium",  # ALPH
    "ALEPHIUM": "alephium",
}

async def get_coin_price_usd(coin_id: str) -> float:
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        return float(data.get(coin_id, {}).get("usd", 0.0))

async def get_algo_price_usd(algo: str) -> float:
    coin_id = COIN_ID_BY_ALGO.get(algo.upper())
    if not coin_id:
        return 0.0
    return await get_coin_price_usd(coin_id)


