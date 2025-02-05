from functools import wraps
from fastapi import HTTPException, status

from trading_execution_system.db.settings import TradeORMRepository
from trading_execution_system.models.user import UserRole
from trading_execution_system.services.trade import TradeService


trade_repo = TradeORMRepository()
trade_service = TradeService(trade_repo)


# TODO: I need to implemnent proper RBAC , similar to this and store the user session data , as well as issue jwt tokens
def any_user_only(func):
    """
    Decorator to ensure the current user is a requester.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if current_user.role != UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only requesters can perform this action.",
            )
        return func(*args, **kwargs)

    return wrapper


def requester_only(func):
    """
    Decorator to ensure the current user is a requester.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        trade_id = kwargs.get("trade_id")
        if (
            current_user.role != UserRole.USER
            and current_user.id != trade_service.get_trade_user(trade_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only requesters can perform this action.",
            )
        return func(*args, **kwargs)

    return wrapper


def admin_only(func):
    """
    Decorator to ensure the current user is an approver.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only approvers can perform this action.",
            )
        return func(*args, **kwargs)

    return wrapper


def requester_or_approver(func):
    """
    Decorator to ensure the current user is either a requester or an approver.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        trade_id = kwargs.get("trade_id")
        if (
            current_user.id != trade_service.get_trade_user(trade_id)
            and current_user.role != UserRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only requesters or approvers can perform this action.",
            )
        return func(*args, **kwargs)

    return wrapper
