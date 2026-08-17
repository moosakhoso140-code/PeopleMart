from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float

from database import Base


class AddItem(BaseModel):
    ItemName:str
    ItemDescription:str
    ItemImage:str
    ItemStock:int
    ItemPrice:float
    ItemGroup:str




class orderItems(Base):
    __tablename__ = "Order"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)  # Make sure it's customer_name (u, not o)
    phone = Column(String)
    address = Column(String)
    item_name = Column(String)
    quantity = Column(Integer)
    total_price = Column(Float)
    status_order = Column(String, default="pending")