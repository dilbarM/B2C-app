from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from contextlib import asynccontextmanager
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
client = MongoClient(MONGO_URL)
database = client["product_catalog_db"]
products_collection = database["products"]

SAMPLE_PRODUCTS = [
    {"product_id": "p1", "name": "Milk", "description": "Fresh cow milk 1L", "price": 50, "category": "Dairy", "image_url": "https://via.placeholder.com/150", "available": True},
    {"product_id": "p2", "name": "Bread", "description": "Whole wheat bread loaf", "price": 35, "category": "Bakery", "image_url": "https://via.placeholder.com/150", "available": True},
    {"product_id": "p3", "name": "Eggs", "description": "Farm fresh eggs 12 pack", "price": 90, "category": "Dairy", "image_url": "https://via.placeholder.com/150", "available": True},
    {"product_id": "p4", "name": "Banana", "description": "Fresh yellow bananas", "price": 40, "category": "Fruits", "image_url": "https://via.placeholder.com/150", "available": True},
    {"product_id": "p5", "name": "Rice", "description": "Basmati rice 1kg", "price": 120, "category": "Grains", "image_url": "https://via.placeholder.com/150", "available": True},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    if products_collection.count_documents({}) == 0:
        products_collection.insert_many(SAMPLE_PRODUCTS)
        print("[startup] Products auto-seeded successfully")
    yield

app = FastAPI(title="Product Catalog Service", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def serialize_product(product: dict) -> dict:
    product["_id"] = str(product["_id"])
    return product

@app.get("/health")
def health_check():
    return {"status": "running", "service": "product-service"}

@app.get("/products", response_model=List[dict])
def get_all_products():
    products = products_collection.find({"available": True})
    return [serialize_product(p) for p in products]

@app.get("/products/{product_id}")
def get_product(product_id: str):
    product = products_collection.find_one({"product_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)

@app.get("/categories")
def get_categories():
    categories = products_collection.distinct("category")
    return {"categories": categories}