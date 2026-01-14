from datetime import datetime, timedelta
from typing import Union, Optional, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi import status
from database.db_sqlalchemy import *
from database import models
from database.load_sqlalchemy import *
import jwt
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
import bcrypt

app = FastAPI()

SECRET_KEY = "super_secret_key" 
ALGORITHM = "HS256"

security = HTTPBearer()

"""
fastapi dev app.py

kolejne: zadanie 7 z tokenów JWT

ctrl + c - zatrzymanie serwera
pip list - lista zainstalowanych pakietów

Users w bazie: 
{"username": "admin", "password": "admin123"},
{"username": "user1", "password": "password123"},
{"username": "test", "password": "test123"}
"""

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Funkcje do uwierzytelniania
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(username: str, roles: List[str]):
    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "roles": roles  # Dodanie ról do payloadu tokena
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAFIRMOWANE,
            detail="Token has expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAFIRMOWANE,
            detail="Invalid token"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAFIRMOWANE,
            detail="Could not validate credentials"
        )

# Użyj HTTPBearer dla lepszej integracji z Swagger UI
security = HTTPBearer()

# Zależność do weryfikacji tokena i roli ADMIN
def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    # Sprawdzenie czy użytkownik ma rolę ADMIN
    if "ROLE_ADMIN" not in payload.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. ROLE_ADMIN required"
        )
    
    return payload["sub"]

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Model danych
class Movie(BaseModel):
    def __init__(self, movieId: int, title: str, genres: list[str]):
        self.movieId = movieId
        self.title = title
        self.genres = genres

class Link(BaseModel):
    def __init__(self, movieId: int, imdbId: str, tmdbId: str):
        self.movieId = movieId
        self.imdbId = imdbId
        self.tmdbId = tmdbId

class Rating(BaseModel):
    def __init__(self, userId: int, movieId: int, rating: float, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.rating = rating
        self.timestamp = timestamp

class Tag(BaseModel):
    def __init__(self, userId: int, movieId: int, tag: str, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.tag = tag
        self.timestamp = timestamp

# User
class LoginData(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    roles: List[str] = []  # Dodanie pola roles

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    movies_list = db.query(models.Movie).all()
    return movies_list

@app.get("/links")
def get_links(db: Session = Depends(get_db)):
    links_list = db.query(models.Link).all()
    return links_list

@app.get("/ratings")
def get_ratings(db: Session = Depends(get_db)):
    ratings_list = db.query(models.Rating).all()
    return ratings_list

@app.get("/tags")
def get_tags(db: Session = Depends(get_db)):
    tags_list = db.query(models.Tag).all()
    return tags_list

# ZABEZPIECZONY ENDPOINT - tylko dla ROLE_ADMIN
@app.post("/users")
def create_user(
    data: UserCreate, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_admin_user)  # Tylko ADMIN
):
    existing_user = db.query(models.User).filter(models.User.username == data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = hash_password(data.password)
    # Dodanie ról do modelu użytkownika
    db_user = models.User(
        username=data.username, 
        hashed_password=hashed_password,
        roles=data.roles  # Zapisanie ról
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {
        "message": "User created successfully", 
        "username": data.username,
        "roles": data.roles,
        "created_by": current_user
    }

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Pobranie ról użytkownika z bazy danych
    user_roles = getattr(user, 'roles', [])
    
    # Utworzenie tokena z rolami użytkownika
    token = create_jwt_token(data.username, user_roles)
    
    return {"access_token": token, "token_type": "bearer"}