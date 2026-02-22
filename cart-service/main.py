from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import requests
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = MongoClient(os.getenv("MONGO_URL"))
db = client[os.getenv("DATABASE_NAME")]
cart_collection = db["carts"]
order_collection = db["orders"]

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL")


class CartItem(BaseModel):
    user_id: str
    product_id: str
    quantity: int


@app.post("/cart/add")
def add_to_cart(item: CartItem):
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{item.product_id}", timeout=5)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found")

    product = response.json()
    entry = {
        "product_id": item.product_id,
        "name": product.get("name"),
        "price": product.get("price"),
        "quantity": item.quantity
    }

    cart = cart_collection.find_one({"user_id": item.user_id})
    if cart:
        cart_collection.update_one(
            {"user_id": item.user_id},
            {"$push": {"items": entry}}
        )
    else:
        cart_collection.insert_one({
            "user_id": item.user_id,
            "items": [entry]
        })
    return {"message": "Item added to cart"}


@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    cart = cart_collection.find_one({"user_id": user_id}, {"_id": 0})
    if not cart:
        return {"user_id": user_id, "items": [], "total": 0}
    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in cart["items"])
    return {"user_id": user_id, "items": cart["items"], "total": total}


@app.post("/order/{user_id}")
def create_order(user_id: str):
    cart = cart_collection.find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    order_id = str(uuid.uuid4())[:8].upper()
    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in cart["items"])

    order_collection.insert_one({
        "order_id": order_id,
        "user_id": user_id,
        "items": cart["items"],
        "total": total,
        "status": "PLACED",
        "placed_at": datetime.utcnow().isoformat()
    })

    cart_collection.delete_one({"user_id": user_id})

    return {
        "message": "Order placed successfully",
        "order_id": order_id,
        "total": total,
        "status": "PLACED"
    }


@app.get("/orders/{user_id}")
def get_orders(user_id: str):
    orders = list(order_collection.find({"user_id": user_id}, {"_id": 0}))
    return {"orders": orders}