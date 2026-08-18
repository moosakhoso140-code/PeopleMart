import sqlalchemy

from sqlalchemy import Integer, String, Column, Float

from databaseSetup.database import Base


class Item(Base):
    __tablename__ = 'item'
    ItemID =Column(Integer, primary_key=True,autoincrement=True,index=True)
    ItemName=Column(String,nullable=False,index=True)
    ItemDescription=Column(String,nullable=False)
    ItemImage=Column(String,nullable=False)
    ItemGroup=Column(String,nullable=False,index=True)
    ItemStock=Column(Integer,nullable=False,default=0)
    ItemPrice=Column(Float,nullable=False)