from typing import Dict, Any, Optional, List

from trading_execution_system.models.enums import TradeState, TradeAction
from trading_execution_system.models.trade import Trade, TradeDetails
from trading_execution_system.db.settings import TradeORMRepository
from trading_execution_system.models.user import User, UserRole
from trading_execution_system.schemas.trade import TradeStatusResponse
from trading_execution_system.utils.diff import compute_differences
from trading_execution_system.services.state_transitions import ALLOWED_TRANSITIONS


class TradeService:
    def __init__(self, db: TradeORMRepository):
        self.db = db

    def _transition(
        self,
        trade: Trade,
        action: TradeAction,
        user_id: str,
        new_details: Optional[TradeDetails] = None,
    ):
        current_state = trade.state
        allowed = ALLOWED_TRANSITIONS.get(current_state, {})

        # Check if the action is allowed from the current state.
        if action not in allowed:
            raise ValueError(
                f"Action {action.name} not allowed from state {current_state.name}"
            )

        if action == TradeAction.UPDATE and new_details is not None:
            new_details.validate_dates()
            trade.details = new_details

        # Update the trade state and add history.
        trade.state = allowed[action]
        trade.add_history(user_id, action.name, current_state)

        # Save the updated trade to the database.
        self.db.update(trade)

    def submit_trade(self, requester_id: str, details: TradeDetails) -> Trade:
        details.validate_dates()
        trade = Trade(requester_id=requester_id, details=details)
        self.db.create(trade)
        self._transition(trade, TradeAction.SUBMIT, requester_id)
        return trade

    def approve_trade(self, trade_id, user_id: str) -> Trade:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        self._transition(trade, TradeAction.APPROVE, user_id)
        return trade

    def update_trade(
        self, trade_id, current_user: User, new_details: TradeDetails
    ) -> Trade:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")

        # Validate the new details.
        new_details.validate_dates()
        trade.details = new_details

        # move the trade to NEEDS_REAPPROVAL after an update.
        previous_state = trade.state
        trade.state = TradeState.NEEDS_REAPPROVAL
        trade.add_history(current_user.id, "UPDATE", previous_state)

        self.db.update(trade)
        return trade

    def cancel_trade(self, trade_id, current_user: User) -> Trade:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")

        # only allow cancellation if trade has not been Booked
        if trade.state == TradeState.EXECUTED:
            raise ValueError("Trade has already been Booked")

        self._transition(trade, TradeAction.CANCEL, current_user.id)
        return trade

    def send_to_execute(self, trade_id, user_id: str) -> Trade:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        self._transition(trade, TradeAction.SEND_TO_EXECUTE, user_id)
        return trade

    def book_trade(self, trade_id, user_id: str, strike: float) -> Trade:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        trade.details.strike = strike
        self._transition(trade, TradeAction.BOOK, user_id)
        return trade

    def get_history(self, trade_id) -> Any:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        return [record.__dict__ for record in trade.history]

    def compute_diff(self, trade_id, from_index: int, to_index: int) -> Dict[str, Any]:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        if (
            from_index < 0
            or to_index < 0
            or from_index >= len(trade.history)
            or to_index >= len(trade.history)
        ):
            raise ValueError(
                f"Invalid history indices - min index should be 0 and max index should be {len(trade.history) - 1}"
            )
        old_snapshot = trade.history[from_index].details_snapshot
        new_snapshot = trade.history[to_index].details_snapshot
        return compute_differences(old_snapshot, new_snapshot)

    def get_trade(self, trade_id) -> TradeStatusResponse:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        state_str = (
            trade.state.name if hasattr(trade.state, "name") else str(trade.state)
        )
        from trading_execution_system.schemas.trade import TradeStatusResponse

        return TradeStatusResponse(id=trade.id, state=state_str)

    # Add this new method to get the full trade.
    def get_full_trade(self, trade_id) -> Trade:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        return trade

    def get_trade_status(self, trade_id) -> TradeStatusResponse:
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")

        from trading_execution_system.schemas.trade import TradeStatusResponse

        return TradeStatusResponse(id=trade.id, state=trade.state.name)

    def get_all_trades(self, user_id: str, is_admin: bool = False) -> List[Trade]:
        """
        Retrieve all trades.
        """
        # FIXME: This should not return all trades but construct a proper query
        all_trades = self.db.list_all()
        if not is_admin:
            # Filter trades to only those created by this user.
            filtered = [trade for trade in all_trades if trade.requester_id == user_id]
            return filtered
        return all_trades

    def get_trade_user(self, trade_id) -> User:
        # TODO: This doesn't belong to here but was needed until i implement the user model and oath2
        trade = self.db.get(str(trade_id))
        if not trade:
            raise ValueError("Trade not found")
        return trade.requester_id
