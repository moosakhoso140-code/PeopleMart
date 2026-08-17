import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

# Path configuration for Vercel execution environment
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from AddItem import AddItem, orderItems
from Item import Item
from database import get_db, Base, engine
from user import User, Userresponse, UserRegister

# Initialize App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template and static directory absolute paths
templates_path = BASE_DIR / "templates"
static_path = BASE_DIR / "templates" / "static"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Use absolute string path for Jinja2
templates = Jinja2Templates(directory=str(templates_path))


# Safe Database Initialization on Startup
@app.on_event("startup")
def startup_db_client():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization skipped or warning: {e}")


class Auth:
    email: str
    password: str
    name: str = None
    role: str = "client"


class UserLogin(BaseModel):
    email: str
    password: str
    role: Optional[str] = None


class OrderCreate(BaseModel):
    product_id: int
    item_name: str
    quantity: int
    total_price: float
    customer_name: str
    phone: str
    address: str
    status_order: Optional[str] = "pending"


@app.get("/", response_class=HTMLResponse)
def get_all_items(request: Request, db: Session = Depends(get_db)):
    try:
        db_items = db.query(Item).all()
    except Exception as e:
        print(f"Database fetch failed: {e}")
        db_items = []

    return templates.TemplateResponse(
        request=request, name="Item.html", context={"items": db_items}
    )


@app.get("/api/products")
def get_all_products(db: Session = Depends(get_db)):
    db_items = db.query(Item).all()
    return [
        {
            "ItemID": item.ItemID,
            "ItemName": item.ItemName,
            "ItemDescription": item.ItemDescription,
            "ItemImage": item.ItemImage,
            "ItemStock": item.ItemStock,
            "ItemPrice": item.ItemPrice,
            "ItemGroup": item.ItemGroup,
        }
        for item in db_items
    ]


@app.post("/add_item")
def create_item(item: AddItem, db: Session = Depends(get_db)):
    new_itme = Item(**item.model_dump())
    db.add(new_itme)
    db.commit()
    db.refresh(new_itme)
    return {"message": "Item added successfully", "item": new_itme}


@app.post("/api/register", response_model=Userresponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    exiting_user = db.query(User).filter(User.username == user.username).first()
    if exiting_user:
        raise HTTPException(status_code=400, detail="User already exists")

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


@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    userd = db.query(User).filter(User.email == user.email).first()

    if not userd or userd.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    role_str = userd.role.value if hasattr(userd.role, "value") else str(userd.role)

    return {
        "message": f"Welcome back, {userd.username}!",
        "user": {
            "id": userd.id,
            "username": userd.username,
            "email": userd.email,
            "role": role_str.lower().strip(),
        },
    }


@app.post("/api/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(Item).filter(Item.ItemID == order.product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.ItemStock < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient inventory stock")

    try:
        product.ItemStock -= order.quantity

        new_order = orderItems(
            customer_name=order.customer_name,
            phone=order.phone,
            address=order.address,
            item_name=order.item_name,
            quantity=order.quantity,
            total_price=order.total_price,
            status_order=order.status_order,
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return {"message": "Order successfully created", "order_id": new_order.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/orders")
def get_all_orders(db: Session = Depends(get_db)):
    orders = db.query(orderItems).all()
    return orders


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return {"message": "find icon"}