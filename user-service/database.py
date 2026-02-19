from pymongo import MongoClient
MONGO_URI = "mongodb://localhost:27017"

client = MongoClient(MONGO_URI)
db = client["quick_commerce"]
users_collection = db["users"]