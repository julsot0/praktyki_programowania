# test_app.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json

from app import app, get_db
from db_sqlalchemy import Base
from load_sqlalchemy import SessionLocal
import models

# Testowa baza danych
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    from app import hash_password
    
    users = [
        models.User(
            username="admin", 
            hashed_password=hash_password("admin123"),
            roles=["ROLE_ADMIN"]
        ),
        models.User(
            username="user1", 
            hashed_password=hash_password("password123"),
            roles=["ROLE_USER"]
        ),
        models.User(
            username="test", 
            hashed_password=hash_password("test123"),
            roles=["ROLE_USER"]
        ),
    ]
    
    movies = [
        models.Movie(movieId=1, title="Toy Story", genres="Animation|Children|Comedy"),
        models.Movie(movieId=2, title="Jumanji", genres="Adventure|Children|Fantasy"),
        models.Movie(movieId=3, title="Grumpier Old Men", genres="Comedy|Romance"),
    ]
    
    links = [
        models.Link(movieId=1, imdbId="0114709", tmdbId="862"),
        models.Link(movieId=2, imdbId="0113497", tmdbId="8844"),
    ]
    
    ratings = [
        models.Rating(ratingId=1, userId=1, movieId=1, rating=4.0, timestamp=964982703),
        models.Rating(ratingId=2, userId=2, movieId=1, rating=4.5, timestamp=964982247),
        models.Rating(ratingId=3, userId=1, movieId=2, rating=3.0, timestamp=964981895),
    ]
    
    tags = [
        models.Tag(tagId=1, userId=1, movieId=1, tag="funny", timestamp=964982703),
        models.Tag(tagId=2, userId=2, movieId=1, tag="Pixar", timestamp=964982247),
        models.Tag(tagId=3, userId=1, movieId=2, tag="adventure", timestamp=964981895),
    ]
    
    for user in users:
        db.add(user)
    
    for movie in movies:
        db.add(movie)
    
    for link in links:
        db.add(link)
    
    for rating in ratings:
        db.add(rating)
    
    for tag in tags:
        db.add(tag)
    
    db.commit()
    db.close()
    
    yield
    
    # wyczyść
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def admin_token():
    response = client.post("/login", json={"username": "admin", "password": "admin123"})
    return response.json()["access_token"]

@pytest.fixture
def user_token():
    response = client.post("/login", json={"username": "user1", "password": "password123"})
    return response.json()["access_token"]

# Testy
class TestLogin:
    def test_login_success(self):
        response = client.post("/login", json={"username": "admin", "password": "admin123"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_username(self):
        response = client.post("/login", json={"username": "nonexistent", "password": "password"})
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
    
    def test_login_invalid_password(self):
        response = client.post("/login", json={"username": "admin", "password": "wrongpassword"})
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
    
    def test_login_missing_fields(self):
        response = client.post("/login", json={"username": "admin"})
        
        assert response.status_code == 422  # Validation error
    
    def test_login_empty_fields(self):
        response = client.post("/login", json={"username": "", "password": ""})
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

# /users
class TestUsers:
    def test_create_user_with_admin_token(self, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "username": "newuser",
            "password": "newpassword123",
            "roles": ["ROLE_USER"]
        }
        
        response = client.post("/users", json=user_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User created successfully"
        assert data["username"] == "newuser"
        assert data["roles"] == ["ROLE_USER"]
        assert data["created_by"] == "admin"
    
    def test_create_user_without_token(self):
        user_data = {
            "username": "anotheruser",
            "password": "password123",
            "roles": ["ROLE_USER"]
        }
        
        response = client.post("/users", json=user_data)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"
    
    def test_create_user_with_user_token(self, user_token):
        headers = {"Authorization": f"Bearer {user_token}"}
        user_data = {
            "username": "anotheruser2",
            "password": "password123",
            "roles": ["ROLE_USER"]
        }
        
        response = client.post("/users", json=user_data, headers=headers)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions. ROLE_ADMIN required"
    
    def test_create_user_duplicate_username(self, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "username": "admin",
            "password": "password123",
            "roles": ["ROLE_USER"]
        }
        
        response = client.post("/users", json=user_data, headers=headers)
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"

# /user_details
class TestUserDetails:
    def test_get_user_details_with_valid_token(self, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get("/user_details", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "ROLE_ADMIN" in data["roles"]
        assert "issued_at" in data
        assert "expires_at" in data
    
    def test_get_user_details_without_token(self):
        response = client.get("/user_details")
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"
    
    def test_get_user_details_with_invalid_token(self):
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/user_details", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

# /movies
class TestMovies:
    def test_get_movies_list(self):
        # get
        response = client.get("/movies")
        
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 3  # 3 filmy
        assert movies[0]["title"] == "Toy Story"
        assert movies[1]["title"] == "Jumanji"
        assert movies[2]["title"] == "Grumpier Old Men"
    
    def test_get_movie_by_id_exists(self):
        # get
        response = client.get("/movies/1")
        
        assert response.status_code == 200
        movie = response.json()
        assert movie["movieId"] == 1
        assert movie["title"] == "Toy Story"
        assert "Animation" in movie["genres"]
    
    def test_get_movie_by_id_not_exists(self):
        # get
        response = client.get("/movies/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"
    
    def test_create_movie(self):
        # post
        movie_data = {
            "title": "New Test Movie",
            "genres": ["Action", "Adventure"]
        }
        
        response = client.post("/movies", json=movie_data)
        
        assert response.status_code == 200
        movie = response.json()
        assert movie["title"] == "New Test Movie"
        assert "Action|Adventure" == movie["genres"]
        assert movie["movieId"] == 4  # Nowe ID
        
        response = client.get("/movies")
        movies = response.json()
        assert len(movies) == 4
    
    def test_update_movie(self):
        # put
        movie_data = {
            "title": "Updated Movie Title",
            "genres": ["Comedy", "Drama"]
        }
        
        response = client.put("/movies/2", json=movie_data)
        
        assert response.status_code == 200
        movie = response.json()
        assert movie["title"] == "Updated Movie Title"
        assert "Comedy|Drama" == movie["genres"]
        
        response = client.get("/movies/2")
        movie = response.json()
        assert movie["title"] == "Updated Movie Title"
    
    def test_update_movie_partial(self):
        # put
        movie_data = {"title": "Partially Updated"}
        
        response = client.put("/movies/3", json=movie_data)
        
        assert response.status_code == 200
        movie = response.json()
        assert movie["title"] == "Partially Updated"
        assert "Comedy|Romance" == movie["genres"]
    
    def test_update_movie_not_exists(self):
        # put
        movie_data = {"title": "Non-existent"}
        
        response = client.put("/movies/999", json=movie_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"
    
    def test_delete_movie(self):
        # delete
        # najpierw film do usunięcia
        movie_data = {
            "title": "Movie to Delete",
            "genres": ["Test"]
        }
        create_response = client.post("/movies", json=movie_data)
        movie_id = create_response.json()["movieId"]
        
        response = client.delete(f"/movies/{movie_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Movie deleted successfully"
        
        response = client.get(f"/movies/{movie_id}")
        assert response.status_code == 404
    
    def test_delete_movie_not_exists(self):
        # delete
        response = client.delete("/movies/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"

# Testy dla endpointów /links
class TestLinks:
    def test_get_links_list(self):
        # get
        response = client.get("/links")
        
        assert response.status_code == 200
        links = response.json()
        assert len(links) == 2  # 2 linki w fixturach
        assert links[0]["movieId"] == 1
        assert links[0]["imdbId"] == "0114709"
    
    def test_get_link_by_movie_id_exists(self):
        # get
        response = client.get("/links/1")
        
        assert response.status_code == 200
        link = response.json()
        assert link["movieId"] == 1
        assert link["imdbId"] == "0114709"
        assert link["tmdbId"] == "862"
    
    def test_get_link_by_movie_id_not_exists(self):
        # get
        response = client.get("/links/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Link not found"
    
    def test_create_link(self):
        # post
        link_data = {
            "movieId": 3,
            "imdbId": "0113498",
            "tmdbId": "8845"
        }
        
        response = client.post("/links", json=link_data)
        
        assert response.status_code == 200
        link = response.json()
        assert link["movieId"] == 3
        assert link["imdbId"] == "0113498"
        assert link["tmdbId"] == "8845"
        
        response = client.get("/links/3")
        assert response.status_code == 200
    
    def test_update_link(self):
        # put
        link_data = {
            "imdbId": "updated_imdb",
            "tmdbId": "updated_tmdb"
        }
        
        response = client.put("/links/1", json=link_data)
        
        assert response.status_code == 200
        link = response.json()
        assert link["imdbId"] == "updated_imdb"
        assert link["tmdbId"] == "updated_tmdb"
        
        response = client.get("/links/1")
        link = response.json()
        assert link["imdbId"] == "updated_imdb"
    
    def test_update_link_not_exists(self):
        # put
        link_data = {"imdbId": "test"}
        
        response = client.put("/links/999", json=link_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Link not found"
    
    def test_delete_link(self):
        # delete
        response = client.delete("/links/2")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Link deleted successfully"
        
        response = client.get("/links/2")
        assert response.status_code == 404

# Testy dla endpointów /ratings
class TestRatings:
    def test_get_ratings_list(self):
        # get
        response = client.get("/ratings")
        
        assert response.status_code == 200
        ratings = response.json()
        assert len(ratings) == 3  # 3 oceny w fixturach
        assert ratings[0]["ratingId"] == 1
        assert ratings[0]["rating"] == 4.0
    
    def test_get_rating_by_id_exists(self):
        # get
        response = client.get("/ratings/1")
        
        assert response.status_code == 200
        rating = response.json()
        assert rating["ratingId"] == 1
        assert rating["userId"] == 1
        assert rating["movieId"] == 1
        assert rating["rating"] == 4.0
    
    def test_get_rating_by_id_not_exists(self):
        # get
        response = client.get("/ratings/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Rating not found"
    
    def test_create_rating(self):
        # post
        rating_data = {
            "userId": 3,
            "movieId": 3,
            "rating": 5.0,
            "timestamp": 964982000
        }
        
        response = client.post("/ratings", json=rating_data)
        
        assert response.status_code == 200
        rating = response.json()
        assert rating["userId"] == 3
        assert rating["movieId"] == 3
        assert rating["rating"] == 5.0
        assert rating["ratingId"] == 4
        
        response = client.get("/ratings")
        ratings = response.json()
        assert len(ratings) == 4
    
    def test_update_rating(self):
        # put
        rating_data = {
            "rating": 2.5,
            "timestamp": 1000000000
        }
        
        response = client.put("/ratings/1", json=rating_data)
        
        assert response.status_code == 200
        rating = response.json()
        assert rating["rating"] == 2.5
        assert rating["timestamp"] == 1000000000
        
        # Weryfikacja w bazie
        response = client.get("/ratings/1")
        rating = response.json()
        assert rating["rating"] == 2.5
    
    def test_update_rating_not_exists(self):
        # put
        rating_data = {"rating": 1.0}
        
        response = client.put("/ratings/999", json=rating_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Rating not found"
    
    def test_delete_rating(self):
        # delete
        rating_data = {
            "userId": 1,
            "movieId": 2,
            "rating": 3.5,
            "timestamp": 964982000
        }
        create_response = client.post("/ratings", json=rating_data)
        rating_id = create_response.json()["ratingId"]
        
        # Usuń ocenę
        response = client.delete(f"/ratings/{rating_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Rating deleted successfully"
        
        response = client.get(f"/ratings/{rating_id}")
        assert response.status_code == 404

# Testy dla endpointów /tags
class TestTags:
    def test_get_tags_list(self):
        # get
        response = client.get("/tags")
        
        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 3  # 3 tagi w fixturach
        assert tags[0]["tagId"] == 1
        assert tags[0]["tag"] == "funny"
    
    def test_get_tag_by_id_exists(self):
        # get
        response = client.get("/tags/1")
        
        assert response.status_code == 200
        tag = response.json()
        assert tag["tagId"] == 1
        assert tag["userId"] == 1
        assert tag["movieId"] == 1
        assert tag["tag"] == "funny"
    
    def test_get_tag_by_id_not_exists(self):
        # get
        response = client.get("/tags/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"
    
    def test_create_tag(self):
        # post
        tag_data = {
            "userId": 2,
            "movieId": 3,
            "tag": "classic",
            "timestamp": 964982500
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 200
        tag = response.json()
        assert tag["userId"] == 2
        assert tag["movieId"] == 3
        assert tag["tag"] == "classic"
        assert tag["tagId"] == 4
        
        response = client.get("/tags")
        tags = response.json()
        assert len(tags) == 4
    
    def test_update_tag(self):
        # put
        tag_data = {
            "tag": "updated_tag",
            "timestamp": 2000000000
        }
        
        response = client.put("/tags/1", json=tag_data)
        
        assert response.status_code == 200
        tag = response.json()
        assert tag["tag"] == "updated_tag"
        assert tag["timestamp"] == 2000000000
        
        response = client.get("/tags/1")
        tag = response.json()
        assert tag["tag"] == "updated_tag"
    
    def test_update_tag_not_exists(self):
        # put
        tag_data = {"tag": "test"}
        
        response = client.put("/tags/999", json=tag_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"
    
    def test_delete_tag(self):
        # delete
        response = client.delete("/tags/3")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Tag deleted successfully"
        
        response = client.get("/tags/3")
        assert response.status_code == 404

# Testy dla root endpoint
class TestRoot:
    def test_root_endpoint(self):
        # get
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}