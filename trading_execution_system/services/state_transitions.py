from trading_execution_system.models.enums import TradeState, TradeAction

ALLOWED_TRANSITIONS = {
    TradeState.DRAFT: {TradeAction.SUBMIT: TradeState.PENDING_APPROVAL},
    TradeState.PENDING_APPROVAL: {
        TradeAction.APPROVE: TradeState.APPROVED,
        TradeAction.CANCEL: TradeState.CANCELLED,
    },
    TradeState.NEEDS_REAPPROVAL: {
        TradeAction.APPROVE: TradeState.APPROVED,
        TradeAction.CANCEL: TradeState.CANCELLED,
    },
    TradeState.APPROVED: {
        TradeAction.SEND_TO_EXECUTE: TradeState.SENT_TO_COUNTERPARTY,
        TradeAction.CANCEL: TradeState.CANCELLED,
    },
    TradeState.SENT_TO_COUNTERPARTY: {
        TradeAction.BOOK: TradeState.EXECUTED,
        TradeAction.CANCEL: TradeState.CANCELLED,
    },
    TradeState.EXECUTED: {},
    TradeState.CANCELLED: {},
}
