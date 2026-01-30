from datetime import datetime, timedelta
from typing import Union, Optional, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi import status
from db_sqlalchemy import *
import models
from load_sqlalchemy import *
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
        "roles": roles
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

security = HTTPBearer()

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    if "ROLE_ADMIN" not in payload.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. ROLE_ADMIN required"
        )
    
    return payload["sub"]

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Modele danych
class Movie(BaseModel):
    def __init__(self, movieId: int, title: str, genres: list[str]):
        self.movieId = movieId
        self.title = title
        self.genres = genres

class MovieCreate(BaseModel):
    title: str
    genres: List[str]

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    genres: Optional[List[str]] = None

class Link(BaseModel):
    def __init__(self, movieId: int, imdbId: str, tmdbId: str):
        self.movieId = movieId
        self.imdbId = imdbId
        self.tmdbId = tmdbId

class LinkCreate(BaseModel):
    movieId: int
    imdbId: str
    tmdbId: str

class LinkUpdate(BaseModel):
    imdbId: Optional[str] = None
    tmdbId: Optional[str] = None

class Rating(BaseModel):
    def __init__(self, userId: int, movieId: int, rating: float, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.rating = rating
        self.timestamp = timestamp

class RatingCreate(BaseModel):
    userId: int
    movieId: int
    rating: float
    timestamp: int

class RatingUpdate(BaseModel):
    rating: Optional[float] = None
    timestamp: Optional[int] = None

class Tag(BaseModel):
    def __init__(self, userId: int, movieId: int, tag: str, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.tag = tag
        self.timestamp = timestamp

class TagCreate(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: int

class TagUpdate(BaseModel):
    tag: Optional[str] = None
    timestamp: Optional[int] = None

class LoginData(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    roles: List[str] = []

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    movies_list = db.query(models.Movie).all()
    return movies_list

# a. POST
@app.post("/movies")
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    genres_str = "|".join(movie.genres)
    
    db_movie = models.Movie(
        title=movie.title,
        genres=genres_str
    )
    
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

# b. READ (item)
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.movieId == movie_id).first()
    
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return movie

# c. PUT
@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, movie_update: MovieUpdate, db: Session = Depends(get_db)):
    db_movie = db.query(models.Movie).filter(models.Movie.movieId == movie_id).first()
    
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if movie_update.title is not None:
        db_movie.title = movie_update.title
    
    if movie_update.genres is not None:
        db_movie.genres = "|".join(movie_update.genres)
    
    db.commit()
    db.refresh(db_movie)
    return db_movie

# d. DELETE
@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(models.Movie).filter(models.Movie.movieId == movie_id).first()
    
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    db.delete(db_movie)
    db.commit()
    
    return {"message": "Movie deleted successfully"}

@app.get("/links")
def get_links(db: Session = Depends(get_db)):
    links_list = db.query(models.Link).all()
    return links_list

# a. POST
@app.post("/links")
def create_link(link: LinkCreate, db: Session = Depends(get_db)):
    db_link = models.Link(
        movieId=link.movieId,
        imdbId=link.imdbId,
        tmdbId=link.tmdbId
    )
    
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

# b. READ
@app.get("/links/{movie_id}")
def get_link(movie_id: int, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.movieId == movie_id).first()
    
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return link

# c. PUT
@app.put("/links/{movie_id}")
def update_link(movie_id: int, link_update: LinkUpdate, db: Session = Depends(get_db)):
    db_link = db.query(models.Link).filter(models.Link.movieId == movie_id).first()
    
    if db_link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link_update.imdbId is not None:
        db_link.imdbId = link_update.imdbId
    
    if link_update.tmdbId is not None:
        db_link.tmdbId = link_update.tmdbId
    
    db.commit()
    db.refresh(db_link)
    return db_link

# d. DELETE
@app.delete("/links/{movie_id}")
def delete_link(movie_id: int, db: Session = Depends(get_db)):
    db_link = db.query(models.Link).filter(models.Link.movieId == movie_id).first()
    
    if db_link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(db_link)
    db.commit()
    
    return {"message": "Link deleted successfully"}

@app.get("/ratings")
def get_ratings(db: Session = Depends(get_db)):
    ratings_list = db.query(models.Rating).all()
    return ratings_list

# a. POST
@app.post("/ratings")
def create_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    db_rating = models.Rating(
        userId=rating.userId,
        movieId=rating.movieId,
        rating=rating.rating,
        timestamp=rating.timestamp
    )
    
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

# b. READ (item)
@app.get("/ratings/{rating_id}")
def get_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.query(models.Rating).filter(models.Rating.ratingId == rating_id).first()
    
    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    return rating

# c. PUT
@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, rating_update: RatingUpdate, db: Session = Depends(get_db)):
    db_rating = db.query(models.Rating).filter(models.Rating.ratingId == rating_id).first()
    
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    if rating_update.rating is not None:
        db_rating.rating = rating_update.rating
    
    if rating_update.timestamp is not None:
        db_rating.timestamp = rating_update.timestamp
    
    db.commit()
    db.refresh(db_rating)
    return db_rating

# d. DELETE
@app.delete("/ratings/{rating_id}")
def delete_rating(rating_id: int, db: Session = Depends(get_db)):
    db_rating = db.query(models.Rating).filter(models.Rating.ratingId == rating_id).first()
    
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    db.delete(db_rating)
    db.commit()
    
    return {"message": "Rating deleted successfully"}

@app.get("/tags")
def get_tags(db: Session = Depends(get_db)):
    tags_list = db.query(models.Tag).all()
    return tags_list

# a. POST
@app.post("/tags")
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    db_tag = models.Tag(
        userId=tag.userId,
        movieId=tag.movieId,
        tag=tag.tag,
        timestamp=tag.timestamp
    )
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

# b. READ (item)
@app.get("/tags/{tag_id}")
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(models.Tag).filter(models.Tag.tagId == tag_id).first()
    
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag

# c. PUT
@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, tag_update: TagUpdate, db: Session = Depends(get_db)):
    db_tag = db.query(models.Tag).filter(models.Tag.tagId == tag_id).first()
    
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag_update.tag is not None:
        db_tag.tag = tag_update.tag
    
    if tag_update.timestamp is not None:
        db_tag.timestamp = tag_update.timestamp
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

# d. DELETE
@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    db_tag = db.query(models.Tag).filter(models.Tag.tagId == tag_id).first()
    
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(db_tag)
    db.commit()
    
    return {"message": "Tag deleted successfully"}

# tylko dla ROLE_ADMIN
@app.post("/users")
def create_user(
    data: UserCreate, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_admin_user)
):
    existing_user = db.query(models.User).filter(models.User.username == data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = hash_password(data.password)
    db_user = models.User(
        username=data.username, 
        hashed_password=hashed_password,
        roles=data.roles
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
    
    user_roles = getattr(user, 'roles', [])
    token = create_jwt_token(data.username, user_roles)
    
    return {"access_token": token, "token_type": "bearer"}

@app.get("/user_details")
def get_user_details(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    return {
        "username": payload.get("sub"),
        "roles": payload.get("roles", []),
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp")
    }