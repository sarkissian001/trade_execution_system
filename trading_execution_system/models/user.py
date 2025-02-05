from enum import Enum
from pydantic import BaseModel


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "api_user"


class User(BaseModel):
    id: str
    role: UserRole


# TODO: This is a simple user database, i need to create a db model for this to enable sessions and autorisation and rbac
USERS = {
    "User1": User(id="User1", role=UserRole.USER),
    "User2": User(id="User2", role=UserRole.USER),
    "admin": User(id="admin", role=UserRole.ADMIN),
}
