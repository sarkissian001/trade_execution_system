from fastapi import HTTPException, Header
from trading_execution_system.models.user import USERS, User


def get_current_user(x_user_id: str = Header(...)) -> User:
    if x_user_id not in USERS:
        raise HTTPException(status_code=401, detail="User not found")
    return USERS[x_user_id]
