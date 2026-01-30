import csv
from database.models import *
from database.db_sqlalchemy import SessionLocal, engine
from database.app import hash_password

Base.metadata.create_all(bind=engine)
session = SessionLocal()


def _open_csv(path):
    return open(path, encoding="utf-8")


def load_movies():
    with _open_csv("movies.csv") as fh:
        read = list(csv.reader(fh))
        for row in read[1:]:
            movie = Movie(
                movieId=int(row[0]),
                title=row[1],
                genres=row[2],
            )

            session.add(movie)
            session.commit()
            session.refresh(movie)

def load_links():
    with _open_csv("links.csv") as fh:
        read = list(csv.reader(fh))
        for row in read[1:]:
            link = Link(
                movieId = int(row[0]),
                imdbId=row[1],
                tmdbId=row[2],
            )

            session.add(link)
            session.commit()
            session.refresh(link)

def load_ratings():
    with _open_csv("ratings.csv") as fh:
        read = list(csv.reader(fh))
        for row in read[1:]:
            rating = Rating(
                userId=int(row[0]),
                movieId=int(row[1]),
                rating=float(row[2]),
                timestamp=int(row[3]),
            )
            session.add(rating)
            session.commit()
            session.refresh(rating)

def load_tags():
    with _open_csv("tags.csv") as fh:
        read = list(csv.reader(fh))
        for row in read[1:]:
            tag = Tag(
                userId=int(row[0]),
                movieId=int(row[1]),
                tag=row[2],
                timestamp=row[3],
            )
            session.add(tag)
            session.commit()
            session.refresh(tag)

def load_users():
    users = [
        {"username": "admin", "password": "admin123", "roles": ["ROLE_ADMIN"]},
        {"username": "user1", "password": "password123", "roles": ["ROLE_USER"]},
        {"username": "test", "password": "test123", "roles": ["ROLE_USER"]}
    ]
    for user_data in users:
        existing_user = session.query(User).filter(User.username == user_data["username"]).first()
        if not existing_user:
            # Sprawdź czy model User ma pole roles
            if hasattr(User, 'roles'):
                user = User(
                    username=user_data["username"],
                    hashed_password=hash_password(user_data["password"]),
                    roles=user_data.get("roles", ["ROLE_USER"])
                )
            else:
                # stare
                user = User(
                    username=user_data["username"],
                    hashed_password=hash_password(user_data["password"])
                )
            session.add(user)
    
    session.commit()

def load_data():
    
    print("Loading movies...")
    load_movies()

    print("Loading links...")
    load_links()

    print("Loading ratings (this can take a while)...")
    load_ratings()

    print("Loading tags...")
    load_tags()
    

    print("Loading users...")
    load_users()
    
    print("Data import complete.")
    session.close()

if session.query(Movie).first() is None:
    load_data()
    
