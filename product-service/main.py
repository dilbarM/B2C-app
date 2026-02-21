from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import List
import os
load_dotenv()
app = FastAPI()
MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise Exception("MONGO_URL environment variable is not found")
client = MongoClient(MONGO_URL)
database = client["product_catalog_db"]
products_collection = database["products"]

def serialize_product(product: dict) -> dict:
    product["_id"] = str(product["_id"])
    return product

@app.get("/products", response_model=List[dict])
def get_all_products():
    products = products_collection.find({"available": True})
    return [serialize_product(product) for product in products]

@app.get("/products/{product_id}")
def get_product(product_id: str):
    product = products_collection.find_one({"_id": product_id, "available": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)

@app.get("/categories/{category_name}/products", response_model=List[dict])
def fetch_categories():
    categories = products_collection.distinct("category")
    return categories

# @app.post("/seed")
# def seed_products():
#     sample_products = [
#         {
#             "product_id": "p1",
#             "name": "Milk",
#             "description": "Fresh cow milk",
#             "price": 50,
#             "category": "Dairy",
#             "image_url": "https://via.placeholder.com/150",
#             "available": True
#         },
#         {
#             "product_id": "p2",
#             "name": "Bread",
#             "description": "Whole wheat bread",
#             "price": 30,
#             "category": "Bakery",
#             "image_url": "https://via.placeholder.com/150",
#             "available": True
#         }
#     ]

#     products_collection.insert_many(sample_products)
#     return {"message": "Products inserted successfully"}