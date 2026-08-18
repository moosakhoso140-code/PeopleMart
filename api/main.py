from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Form,Request
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.cors import CORSMiddleware

from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from databaseSetup.AddItem import AddItem, orderItems
from Model.Item import Item

from databaseSetup.database import get_db, Base, engine, password
from databaseSetup.user import User, Userresponse, UserRegister
app=FastAPI()
Base.metadata.create_all(bind=engine)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

templates=Jinja2Templates(directory="templates")



class Auth():
    email: str
    password: str
    name:str=None
    role:str="client"

class UserLogin(BaseModel):
    email: str
    password: str
    role:Optional[str]=None

class OrderCreate(BaseModel):
    product_id: int  # Changed from item_id to match frontend payload
    item_name: str
    quantity: int
    total_price: float
    customer_name: str
    phone: str
    address: str
    status_order: Optional[str] = "pending"
@app.get("/", response_class=HTMLResponse)
def get_all_items(request: Request, db: Session = Depends(get_db)):

    db_items = db.query(Item).all()

    # 2. 'request' object aur 'items' (list) ko HTML template ko pass karein
    return templates.TemplateResponse(
    request=request, name="Item.html", context={"items": db_items}
    )


@app.get("/api/products")
def get_all_products(


    db: Session = Depends(get_db)
):
    # Retrieve paginated items
    db_items = db.query(Item).all()
    return [
        {
            "ItemID": item.ItemID,
            "ItemName": item.ItemName,
            "ItemDescription": item.ItemDescription,
            "ItemImage": item.ItemImage,
            "ItemStock": item.ItemStock,
            "ItemPrice": item.ItemPrice,
            "ItemGroup":item.ItemGroup
        }
        for item in db_items
    ]
@app.post("/add_item")
def create_item(item:AddItem,db:Session=Depends(get_db)):

    new_itme=Item(**item.model_dump())
    db.add(new_itme)
    db.commit()
    db.refresh(new_itme)
    return{
        "message": "Item added successfully",
        "item": new_itme
    }


@app.post("/api/register",response_model=Userresponse)
def register(user: UserRegister,db:Session = Depends(get_db)):
    exiting_user =db.query(User).filter(User.username==user.username).first()
    if exiting_user:
        raise HTTPException(status_code=400,detail="User already exists")

    db_user = User(
        username=user.username,
        email=user.email,
        password=user.password,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
 # ya UserLoginSchema
# @app.post("/api/login")
# def login(user: UserLogin, db: Session = Depends(get_db)):
#     # 1. Fetch user by email only
#     userd = db.query(User).filter(User.email == user.email, User.role == user.role).first()
#
#     # 2. Check if user exists and password matches
#     if not userd or userd.password != user.password:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Incorrect email or password"
#         )
#
#     role_value = userd.role.value if hasattr(userd.role, 'value') else str(userd.role)
#
#     return {
#         "message": f"Welcome back, {userd.username}!",
#         "user": {
#             "id": userd.id,
#             "username": userd.username,
#             "email": userd.email,
#             "role": role_value.lower().strip()
#         },
#     }
@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):



    userd = db.query(User).filter(User.email == user.email).first()

    if not userd:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )




    # Check password matching
    if userd.password != user.password:
        print("--> Error: Password mismatch!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )


    role_str = userd.role.value if hasattr(userd.role, 'value') else str(userd.role)



    return {
        "message": f"Welcome back, {userd.username}!",
        "user": {
            "id": userd.id,
            "username": userd.username,
            "email": userd.email,
            "role": role_str.lower().strip()
        }
    }






@app.post("/api/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # 1. Product check (using order.product_id from Pydantic schema)
    product = db.query(Item).filter(Item.ItemID == order.product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. Stock inventory check
    if product.ItemStock < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient inventory stock")

    try:
        # 3. Deduct stock using the correct database attribute name (ItemStock)
        product.ItemStock -= order.quantity

        new_order = orderItems(
            customer_name=order.customer_name,  # Fixed typo
            phone=order.phone,  # Matches column name
            address=order.address,
            item_name=order.item_name,
            quantity=order.quantity,
            total_price=order.total_price,  # Matches column name
            status_order=order.status_order
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return {"message": "Order successfully created", "order_id": new_order.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/orders")
def get_all_orders(db:Session = Depends(get_db)):
    orders = db.query(orderItems).all()
    return orders