import datetime
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from trading_execution_system.models.enums import TradeState


@dataclass
class TradeDetails:
    trading_entity: str
    counterparty: str
    direction: str
    style: str  # forward or a swap
    currency: str
    notional_amount: float
    underlying: List[str]
    trade_date: datetime.date
    value_date: datetime.date
    delivery_date: datetime.date
    strike: Optional[float] = None

    def validate_dates(self):
        if not (self.trade_date <= self.value_date <= self.delivery_date):
            raise ValueError("Trade date must be <= value date <= delivery date.")


@dataclass
class HistoryRecord:
    timestamp: datetime.datetime
    user_id: str
    action: str
    previous_state: TradeState
    new_state: TradeState
    details_snapshot: Dict[str, Any]


@dataclass
class Trade:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    requester_id: str = ""
    details: TradeDetails = None
    state: TradeState = TradeState.DRAFT
    history: List[HistoryRecord] = field(default_factory=list)

    def add_history(self, user_id: str, action: str, previous_state: TradeState):
        record = HistoryRecord(
            timestamp=datetime.datetime.utcnow(),
            user_id=user_id,
            action=action,
            previous_state=previous_state,
            new_state=self.state,
            details_snapshot=asdict(self.details) if self.details else {},
        )
        self.history.append(record)
