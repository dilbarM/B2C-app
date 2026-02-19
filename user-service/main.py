from fastapi import FastAPI, HTTPException
from database import users_collection
from passlib.context import CryptContext
from schemas import UserCreate
from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()
app=FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password[:72])

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
def login(user: UserCreate):
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user:
        raise HTTPException(status_code=400, detail="invalid credentials")
    if not verify_password(users_collection.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="invalid credentials")
    
    access_token = create_access_token({"sub": users_collection.email})
    return {"access_token": access_token, 
            "token_type": "bearer"}


@app.post("/users")
def register(user: UserCreate):
    exist_user = users_collection.find_one({"email": user.email})
    if exist_user:
        return {"message": "Email already registered"}
    hashed_password = hash_password(user.password)

    users_collection.user_data.insert_one = {
        "name":user.name,
        "email":user.email,
        "password":hashed_password
    }
    return {"message": "User registered successfully"}


@app.get("/")
def root():
    return {"message": "user service"}

@app.get("/test-db")
def test_db():
    users_collection.insert_one({"name":"John"})
    return {"message": "inserted successfully"}

@app.get("/users")
def get_users():
    users = list(users_collection.find({}, {"_id": 0}))
    return users