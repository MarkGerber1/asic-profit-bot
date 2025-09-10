from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, conint, confloat, RootModel


class AlgorithmOut(BaseModel):
    id: str
    name: str
    unit: str
    paying_btc_per_unit_per_day: float = Field(..., ge=0)


class HashrateIn(BaseModel):
    value: confloat(gt=0)
    unit: Literal["H", "KH", "MH", "GH", "TH", "PH", "EH"]


class FeesIn(BaseModel):
    marketplace_pct: confloat(ge=0, le=10) = 2.0
    pool_pct: confloat(ge=0, le=10) = 0.0


class ElectricityIn(BaseModel):
    value: confloat(ge=0, le=200)
    currency: Literal["RUB", "USD", "EUR", "CZK"] = "RUB"


class CalculateRequest(BaseModel):
    mode: Literal["algo", "device"] = "algo"
    algoId: str
    deviceId: Optional[str] = None
    hashrate: HashrateIn
    power_w: conint(ge=1) = 120
    electricity: ElectricityIn
    fees: FeesIn = FeesIn()
    uptime_pct: confloat(ge=50, le=100) = 98.0
    fiat: Literal["RUB", "USD", "EUR", "CZK"] = "RUB"
    periods: Optional[list[Literal["1h", "24h", "168h", "720h"]]] = None


class PeriodValues(BaseModel):
    revenue_btc: float
    revenue_fiat: float
    electricity_cost_fiat: float
    fees_fiat: float
    net_profit_fiat: float


class PeriodsOut(RootModel[Dict[str, PeriodValues]]):
    pass


class CalculateResponse(BaseModel):
    algoId: str
    unit: str
    btc_price: Dict[str, float]
    periods: PeriodsOut
    disclaimer: str


class DeviceOut(BaseModel):
    id: str
    vendor: str
    model: str
    algoId: str
    nominal_hashrate_value: float
    unit: Literal["H", "KH", "MH", "GH", "TH", "PH", "EH"]
    power_w: int
    price_fiat: float | None = None


