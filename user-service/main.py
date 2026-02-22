from fastapi import FastAPI, HTTPException
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from database import users_collection
from schemas import Login, UserCreate
from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import bcrypt
import os
load_dotenv()
app=FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
def login(user: Login):
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user:
        raise HTTPException(status_code=400, detail="invalid credentials")
    if not verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="invalid credentials")
    
    access_token = create_access_token({"sub": existing_user["email"]})
    return {"access_token": access_token, 
            "token_type": "bearer"}


@app.post("/users")
def register(user: UserCreate):
    exist_user = users_collection.find_one({"email": user.email})
    if exist_user:
        return {"message": "Email already registered"}
    hashed_password = hash_password(user.password)

    user_data = {
        "name":user.name,
        "email":user.email,
        "password":hashed_password
    }
    users_collection.insert_one(user_data)
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


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="invalid token")
        user = users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")
 
@app.get("/profile")
def read_profile(current_user:dict = Depends(get_current_user)):
    return {
            "name": current_user.get("name"), 
            "email": current_user["email"]
            }
