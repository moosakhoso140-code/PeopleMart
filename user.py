from pydantic import BaseModel,Field

from sqlalchemy import Column, String, Integer

from database import Base


class User(Base):
    __tablename__="users"
    id = Column(
        Integer,
        primary_key=True,

    )
    username=Column(String,nullable=False)
    email=Column(String,nullable=False,unique=True)
    password=Column(String,nullable=False)
    role=Column(String,nullable=False)



class Userresponse(BaseModel):
    id:int
    username:str
    email:str
    role:str

    class Config:
        from_attributes = (
            True
        )

class UserRegister(BaseModel):
    username:str
    role:str="client"
    email:str
    password:str=Field(min_length=8,max_length=20,nullable=False)