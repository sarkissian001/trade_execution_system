from typing import List
from fastapi import APIRouter, HTTPException, Depends
from trading_execution_system.models.user import USERS, User, UserRole
from trading_execution_system.core.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[User])
def list_users(current_user: User = Depends(get_current_user)):
    """
    List all users.
    Only users with the ADMIN role can view all users.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorised to view all users")
    return list(USERS.values())
