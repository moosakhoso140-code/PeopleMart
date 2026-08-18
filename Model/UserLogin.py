from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    Admin = "Admin"
    User = "User"


class Login(BaseModel):
     
    username: str
    password: str
