from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

from pydantic import BaseModel, validator


class TradeDetailsSchema(BaseModel):
    trading_entity: str
    counterparty: str
    direction: str  # can be buy or sell
    style: str
    currency: str
    notional_amount: float
    underlying: List[str]
    trade_date: date
    value_date: date
    delivery_date: date
    strike: Optional[float] = None

    @validator("value_date")
    def check_trade_date(cls, v, values):
        if "trade_date" in values and v < values["trade_date"]:
            raise ValueError("value_date must be after or equal to trade_date")
        return v

    @validator("delivery_date")
    def check_value_date(cls, v, values):
        if "value_date" in values and v < values["value_date"]:
            raise ValueError("delivery_date must be after or equal to value_date")
        return v


class TradeCreateRequest(BaseModel):
    requester_id: str
    details: TradeDetailsSchema


class TradeActionRequest(BaseModel):
    user_id: str
    details: Optional[TradeDetailsSchema] = None


class TradeResponse(BaseModel):
    id: UUID
    state: str
    details: TradeDetailsSchema
    history: List[Dict[str, Any]]


class TradeHistoryResponse(BaseModel):
    history: List[Dict[str, Any]]


class TradeDiffResponse(BaseModel):
    differences: Dict[str, Any]


class TradeBookRequest(BaseModel):
    strike: float


class TradeStatusResponse(BaseModel):
    id: UUID
    state: str
