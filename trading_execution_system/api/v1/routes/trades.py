from typing import List

from fastapi import APIRouter, HTTPException, Query, Depends
from uuid import UUID

from trading_execution_system.core.rbac import (
    any_user_only,
    admin_only,
    requester_only,
    requester_or_approver,
)
from trading_execution_system.schemas.trade import (
    TradeCreateRequest,
    TradeActionRequest,
    TradeResponse,
    TradeHistoryResponse,
    TradeDiffResponse,
    TradeBookRequest,
    TradeStatusResponse,
)
from trading_execution_system.models.trade import TradeDetails
from trading_execution_system.db.settings import TradeORMRepository
from trading_execution_system.services.trade import TradeService
from trading_execution_system.core.dependencies import get_current_user
from trading_execution_system.models.user import User, UserRole

router = APIRouter()

trade_repo = TradeORMRepository()
trade_service = TradeService(trade_repo)


@router.post("/", response_model=TradeResponse)
@any_user_only
def submit_trade(
    request: TradeCreateRequest, current_user: User = Depends(get_current_user)
):
    try:
        details = TradeDetails(**request.details.model_dump())
        trade = trade_service.submit_trade(current_user.id, details)
        return TradeResponse(
            id=trade.id,
            state=trade.state.name,
            details=request.details,
            history=[record.__dict__ for record in trade.history],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trade_id}/approve", response_model=TradeResponse)
@admin_only
def approve_trade(trade_id: UUID, current_user: User = Depends(get_current_user)):
    try:
        trade = trade_service.approve_trade(trade_id, current_user.id)
        return TradeResponse(
            id=trade.id,
            state=trade.state.name,
            details=trade.details.__dict__,
            history=[record.__dict__ for record in trade.history],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trade_id}/update", response_model=TradeResponse)
@requester_only
def update_trade(
    trade_id: UUID,
    request: TradeActionRequest,
    current_user: User = Depends(get_current_user),
):
    if request.details is None:
        raise HTTPException(
            status_code=400, detail="Updated trade details are required."
        )

    try:
        new_details = TradeDetails(**request.details.model_dump())
        # Pass the entire current_user to the service.
        trade = trade_service.update_trade(trade_id, current_user, new_details)
        return TradeResponse(
            id=trade.id,
            state=trade.state.name,
            details=trade.details.__dict__,
            history=[record.__dict__ for record in trade.history],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trade_id}/cancel", response_model=TradeResponse)
@requester_or_approver
def cancel_trade(trade_id: UUID, current_user: User = Depends(get_current_user)):
    try:

        trade = trade_service.cancel_trade(trade_id, current_user)

        return TradeResponse(
            id=trade.id,
            state=trade.state.name,
            details=trade.details.__dict__,
            history=[record.__dict__ for record in trade.history],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trade_id}/send_to_execute", response_model=TradeResponse)
@admin_only
def send_to_execute(trade_id: UUID, current_user: User = Depends(get_current_user)):
    try:

        trade = trade_service.send_to_execute(trade_id, current_user.id)
        return TradeResponse(
            id=trade.id,
            state=trade.state.name,
            details=trade.details.__dict__,
            history=[record.__dict__ for record in trade.history],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trade_id}/book", response_model=TradeResponse)
@requester_or_approver
def book_trade(
    trade_id: UUID,
    request: TradeBookRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        trade = trade_service.book_trade(trade_id, current_user.id, request.strike)
        return TradeResponse(
            id=trade.id,
            state=trade.state.name,
            details=trade.details.__dict__,
            history=[record.__dict__ for record in trade.history],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trade_id}/history", response_model=TradeHistoryResponse)
@requester_or_approver
def get_trade_history(trade_id: UUID, current_user: User = Depends(get_current_user)):
    try:
        history = trade_service.get_history(trade_id)
        return TradeHistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trade_id}/diff", response_model=TradeDiffResponse)
@requester_or_approver
def get_trade_diff(
    trade_id: UUID,
    from_index: int = Query(..., ge=0, description="History index to compare from"),
    to_index: int = Query(..., ge=0, description="History index to compare to"),
    current_user: User = Depends(get_current_user),
):
    try:
        diffs = trade_service.compute_diff(trade_id, from_index, to_index)
        return TradeDiffResponse(differences=diffs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trade_id}/status", response_model=TradeStatusResponse)
@requester_or_approver
def get_trade_status_endpoint(
    trade_id: UUID, current_user: User = Depends(get_current_user)
):
    try:
        trade_status = trade_service.get_trade_status(trade_id)
        return trade_status
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TradeResponse])
def get_all_trades(current_user: User = Depends(get_current_user)):
    """
    Retrieve all trades for the current user.
    """
    try:
        is_admin = current_user.role == UserRole.ADMIN
        trades = trade_service.get_all_trades(current_user.id, is_admin)

        return [
            TradeResponse(
                id=trade.id,
                state=trade.state.name,
                details=trade.details.__dict__,
                history=[record.__dict__ for record in trade.history],
            )
            for trade in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
