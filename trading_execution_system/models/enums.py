from enum import Enum, auto


class TradeState(Enum):
    DRAFT = auto()
    PENDING_APPROVAL = auto()
    NEEDS_REAPPROVAL = auto()
    APPROVED = auto()
    SENT_TO_COUNTERPARTY = auto()
    EXECUTED = auto()
    CANCELLED = auto()


class TradeAction(Enum):
    SUBMIT = auto()
    APPROVE = auto()
    UPDATE = auto()
    CANCEL = auto()
    SEND_TO_EXECUTE = auto()
    BOOK = auto()
