from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from dotenv import load_dotenv
from pydantic import BaseModel
import os
import requests

load_dotenv()

app = FastAPI()

MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL")

client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]

cart_collection = db["carts"]
order_collection = db["orders"]


class CartItem(BaseModel):
    user_id: str
    product_id: str
    quantity: int


@app.post("/cart/add")
def add_to_cart(item: CartItem):
    
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{item.product_id}")

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found")

    cart = cart_collection.find_one({"user_id": item.user_id})

    if cart:
        cart_collection.update_one(
            {"user_id": item.user_id},
            {"$push": {"items": item.dict()}}
        )
    else:
        cart_collection.insert_one({
            "user_id": item.user_id,
            "items": [item.dict()]
        })

    return {"message": "Item added to cart"}


@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    cart = cart_collection.find_one({"user_id": user_id}, {"_id": 0})
    if not cart:
        return {"items": []}
    return cart


@app.post("/order/{user_id}")
def create_order(user_id: str):
    cart = cart_collection.find_one({"user_id": user_id})

    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    order_collection.insert_one({
        "user_id": user_id,
        "items": cart["items"],
        "status": "created"
    })

    cart_collection.delete_one({"user_id": user_id})

    return {"message": "Order created successfully"}