from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URL", "mongodb://mongo:27017"))
db = mongo_client["qc_delivery"]
tracking_collection = db["tracking"]

DELIVERY_STAGES = ["PLACED", "PACKED", "OUT_FOR_DELIVERY", "DELIVERED"]

app = FastAPI(title="Delivery Tracking Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def now() -> str:
    return datetime.utcnow().isoformat()

@app.get("/health")
def health_check():
    return {"status": "running", "service": "delivery-service"}

@app.post("/order/{order_id}/track")
def start_tracking(order_id: str):
    if tracking_collection.find_one({"order_id": order_id}):
        raise HTTPException(status_code=409, detail=f"Order {order_id} is already being tracked")

    tracking_collection.insert_one({
        "order_id": order_id,
        "current_status": "PLACED",
        "history": [{"status": "PLACED", "updated_at": now()}],
        "created_at": now(),
        "last_updated": now()
    })

    return {"message": "Tracking started", "order_id": order_id, "current_status": "PLACED"}

@app.get("/order/{order_id}/status")
def get_delivery_status(order_id: str):
    record = tracking_collection.find_one({"order_id": order_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail=f"No tracking found for order '{order_id}'")
    return record

@app.post("/order/{order_id}/update-status")
def advance_delivery_status(order_id: str):
    record = tracking_collection.find_one({"order_id": order_id})
    if not record:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")

    current_status = record.get("current_status")

    if current_status == "DELIVERED":
        return {"message": "Order already delivered", "order_id": order_id, "current_status": "DELIVERED"}

    next_status = DELIVERY_STAGES[DELIVERY_STAGES.index(current_status) + 1]
    updated_history = record.get("history", [])
    updated_history.append({"status": next_status, "updated_at": now()})

    tracking_collection.update_one(
        {"order_id": order_id},
        {"$set": {"current_status": next_status, "history": updated_history, "last_updated": now()}}
    )

    return {
        "message": "Status updated",
        "order_id": order_id,
        "previous_status": current_status,
        "current_status": next_status
    }