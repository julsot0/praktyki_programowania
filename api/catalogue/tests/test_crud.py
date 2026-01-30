import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Naprawić importy :)
from app import app
from database import Base, get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture dla bazy danych
@pytest.fixture(scope="function")
def db_session():
    # Tworzymy tabele
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Fixture dla klienta testowego
@pytest.fixture(scope="function")
def test_client(db_session):
    # Nadpisujemy zależność get_db, aby używała testowej bazy
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Czyścimy override po teście
    app.dependency_overrides.clear()

# Fixtury danych testowych
@pytest.fixture
def sample_movie_data():
    return {
        "title": "Test Movie",
        "genres": ["Action", "Adventure"]
    }

@pytest.fixture
def sample_link_data():
    return {
        "movieId": 1,
        "imdbId": "tt1234567",
        "tmdbId": "12345"
    }

@pytest.fixture
def sample_rating_data():
    return {
        "userId": 1,
        "movieId": 1,
        "rating": 4.5,
        "timestamp": 964982703
    }

@pytest.fixture
def sample_tag_data():
    return {
        "userId": 1,
        "movieId": 1,
        "tag": "awesome",
        "timestamp": 964982703
    }

# ===== TESTS FOR MOVIES =====
class TestMoviesAPI:
    """Testy dla endpointów /movies"""
    
    def test_get_all_movies_empty(self, test_client):
        """Test GET /movies gdy baza jest pusta"""
        response = test_client.get("/movies")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_and_get_movie(self, test_client, sample_movie_data):
        """Test POST i GET dla filmów"""
        # POST - tworzenie filmu
        response = test_client.post("/movies", json=sample_movie_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_movie_data["title"]
        assert data["genres"] == "|".join(sample_movie_data["genres"])
        assert "movieId" in data
        
        movie_id = data["movieId"]
        
        # GET wszystkich filmów
        response = test_client.get("/movies")
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 1
        assert movies[0]["movieId"] == movie_id
        
        # GET pojedynczego filmu
        response = test_client.get(f"/movies/{movie_id}")
        assert response.status_code == 200
        movie = response.json()
        assert movie["movieId"] == movie_id
        assert movie["title"] == sample_movie_data["title"]
    
    def test_get_nonexistent_movie(self, test_client):
        """Test GET /movies/{id} dla nieistniejącego filmu"""
        response = test_client.get("/movies/999999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"
    
    def test_update_movie(self, test_client, sample_movie_data):
        """Test PUT dla filmu"""
        # Najpierw tworzymy film
        response = test_client.post("/movies", json=sample_movie_data)
        movie_id = response.json()["movieId"]
        
        # Aktualizujemy film
        update_data = {
            "title": "Updated Title",
            "genres": ["Drama", "Romance"]
        }
        response = test_client.put(f"/movies/{movie_id}", json=update_data)
        
        assert response.status_code == 200
        updated_movie = response.json()
        assert updated_movie["title"] == update_data["title"]
        assert updated_movie["genres"] == "|".join(update_data["genres"])
        
        # Sprawdzamy czy zmiana została zapisana
        response = test_client.get(f"/movies/{movie_id}")
        movie = response.json()
        assert movie["title"] == update_data["title"]
    
    def test_partial_update_movie(self, test_client, sample_movie_data):
        """Test PUT z częściową aktualizacją"""
        response = test_client.post("/movies", json=sample_movie_data)
        movie_id = response.json()["movieId"]
        
        # Aktualizujemy tylko tytuł
        update_data = {"title": "Only Title Updated"}
        response = test_client.put(f"/movies/{movie_id}", json=update_data)
        
        assert response.status_code == 200
        updated_movie = response.json()
        assert updated_movie["title"] == update_data["title"]
        # Genres powinny pozostać bez zmian
        assert updated_movie["genres"] == "|".join(sample_movie_data["genres"])
    
    def test_delete_movie(self, test_client, sample_movie_data):
        """Test DELETE dla filmu"""
        # Tworzymy film
        response = test_client.post("/movies", json=sample_movie_data)
        movie_id = response.json()["movieId"]
        
        # Usuwamy film
        response = test_client.delete(f"/movies/{movie_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Movie deleted successfully"
        
        # Sprawdzamy czy film został usunięty
        response = test_client.get(f"/movies/{movie_id}")
        assert response.status_code == 404
        
        # Sprawdzamy czy lista filmów jest pusta
        response = test_client.get("/movies")
        assert len(response.json()) == 0

# ===== TESTS FOR LINKS =====
class TestLinksAPI:
    """Testy dla endpointów /links"""
    
    def test_create_and_get_link(self, test_client, sample_link_data):
        """Test POST i GET dla linków"""
        # POST - tworzenie linku
        response = test_client.post("/links", json=sample_link_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["movieId"] == sample_link_data["movieId"]
        assert data["imdbId"] == sample_link_data["imdbId"]
        
        movie_id = data["movieId"]
        
        # GET wszystkich linków
        response = test_client.get("/links")
        assert response.status_code == 200
        links = response.json()
        assert len(links) == 1
        assert links[0]["movieId"] == movie_id
        
        # GET pojedynczego linku
        response = test_client.get(f"/links/{movie_id}")
        assert response.status_code == 200
        link = response.json()
        assert link["movieId"] == movie_id
    
    def test_get_nonexistent_link(self, test_client):
        """Test GET /links/{id} dla nieistniejącego linku"""
        response = test_client.get("/links/999999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Link not found"
    
    def test_update_link(self, test_client, sample_link_data):
        """Test PUT dla linku"""
        # Tworzymy link
        response = test_client.post("/links", json=sample_link_data)
        movie_id = response.json()["movieId"]
        
        # Aktualizujemy link
        update_data = {
            "imdbId": "tt7654321",
            "tmdbId": "54321"
        }
        response = test_client.put(f"/links/{movie_id}", json=update_data)
        
        assert response.status_code == 200
        updated_link = response.json()
        assert updated_link["imdbId"] == update_data["imdbId"]
        
        # Sprawdzamy czy zmiana została zapisana
        response = test_client.get(f"/links/{movie_id}")
        link = response.json()
        assert link["imdbId"] == update_data["imdbId"]
    
    def test_delete_link(self, test_client, sample_link_data):
        """Test DELETE dla linku"""
        # Tworzymy link
        response = test_client.post("/links", json=sample_link_data)
        movie_id = response.json()["movieId"]
        
        # Usuwamy link
        response = test_client.delete(f"/links/{movie_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Link deleted successfully"
        
        # Sprawdzamy czy link został usunięty
        response = test_client.get(f"/links/{movie_id}")
        assert response.status_code == 404

# ===== TESTS FOR RATINGS =====
class TestRatingsAPI:
    """Testy dla endpointów /ratings"""
    
    def test_create_and_get_rating(self, test_client, sample_rating_data):
        """Test POST i GET dla ratingów"""
        # POST - tworzenie ratingu
        response = test_client.post("/ratings", json=sample_rating_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["userId"] == sample_rating_data["userId"]
        assert data["rating"] == sample_rating_data["rating"]
        assert "ratingId" in data
        
        rating_id = data["ratingId"]
        
        # GET wszystkich ratingów
        response = test_client.get("/ratings")
        assert response.status_code == 200
        ratings = response.json()
        assert len(ratings) == 1
        assert ratings[0]["ratingId"] == rating_id
        
        # GET pojedynczego ratingu
        response = test_client.get(f"/ratings/{rating_id}")
        assert response.status_code == 200
        rating = response.json()
        assert rating["ratingId"] == rating_id
    
    def test_get_nonexistent_rating(self, test_client):
        """Test GET /ratings/{id} dla nieistniejącego ratingu"""
        response = test_client.get("/ratings/999999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Rating not found"
    
    def test_update_rating(self, test_client, sample_rating_data):
        """Test PUT dla ratingu"""
        # Tworzymy rating
        response = test_client.post("/ratings", json=sample_rating_data)
        rating_id = response.json()["ratingId"]
        
        # Aktualizujemy rating
        update_data = {
            "rating": 5.0,
            "timestamp": 964982704
        }
        response = test_client.put(f"/ratings/{rating_id}", json=update_data)
        
        assert response.status_code == 200
        updated_rating = response.json()
        assert updated_rating["rating"] == update_data["rating"]
        
        # Sprawdzamy czy zmiana została zapisana
        response = test_client.get(f"/ratings/{rating_id}")
        rating = response.json()
        assert rating["rating"] == update_data["rating"]
    
    def test_delete_rating(self, test_client, sample_rating_data):
        """Test DELETE dla ratingu"""
        # Tworzymy rating
        response = test_client.post("/ratings", json=sample_rating_data)
        rating_id = response.json()["ratingId"]
        
        # Usuwamy rating
        response = test_client.delete(f"/ratings/{rating_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Rating deleted successfully"
        
        # Sprawdzamy czy rating został usunięty
        response = test_client.get(f"/ratings/{rating_id}")
        assert response.status_code == 404

# ===== TESTS FOR TAGS =====
class TestTagsAPI:
    """Testy dla endpointów /tags"""
    
    def test_create_and_get_tag(self, test_client, sample_tag_data):
        """Test POST i GET dla tagów"""
        # POST - tworzenie tagu
        response = test_client.post("/tags", json=sample_tag_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["tag"] == sample_tag_data["tag"]
        assert "tagId" in data
        
        tag_id = data["tagId"]
        
        # GET wszystkich tagów
        response = test_client.get("/tags")
        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 1
        assert tags[0]["tagId"] == tag_id
        
        # GET pojedynczego tagu
        response = test_client.get(f"/tags/{tag_id}")
        assert response.status_code == 200
        tag = response.json()
        assert tag["tagId"] == tag_id
    
    def test_get_nonexistent_tag(self, test_client):
        """Test GET /tags/{id} dla nieistniejącego tagu"""
        response = test_client.get("/tags/999999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"
    
    def test_update_tag(self, test_client, sample_tag_data):
        """Test PUT dla tagu"""
        # Tworzymy tag
        response = test_client.post("/tags", json=sample_tag_data)
        tag_id = response.json()["tagId"]
        
        # Aktualizujemy tag
        update_data = {
            "tag": "amazing",
            "timestamp": 964982704
        }
        response = test_client.put(f"/tags/{tag_id}", json=update_data)
        
        assert response.status_code == 200
        updated_tag = response.json()
        assert updated_tag["tag"] == update_data["tag"]
        
        # Sprawdzamy czy zmiana została zapisana
        response = test_client.get(f"/tags/{tag_id}")
        tag = response.json()
        assert tag["tag"] == update_data["tag"]
    
    def test_delete_tag(self, test_client, sample_tag_data):
        """Test DELETE dla tagu"""
        # Tworzymy tag
        response = test_client.post("/tags", json=sample_tag_data)
        tag_id = response.json()["tagId"]
        
        # Usuwamy tag
        response = test_client.delete(f"/tags/{tag_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Tag deleted successfully"
        
        # Sprawdzamy czy tag został usunięty
        response = test_client.get(f"/tags/{tag_id}")
        assert response.status_code == 404

# ===== TESTS FOR EDGE CASES =====
class TestEdgeCases:
    """Testy przypadków brzegowych"""
    
    def test_create_duplicate_link(self, test_client, sample_link_data):
        """Test tworzenia duplikatu linku (powinien zwrócić 400)"""
        # Pierwsze tworzenie
        response = test_client.post("/links", json=sample_link_data)
        assert response.status_code == 200
        
        # Próba stworzenia drugiego linku z tym samym movieId
        response = test_client.post("/links", json=sample_link_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_update_nonexistent_resource(self, test_client):
        """Test aktualizacji nieistniejącego zasobu"""
        update_data = {"title": "New Title"}
        response = test_client.put("/movies/999999", json=update_data)
        assert response.status_code == 404
    
    def test_delete_nonexistent_resource(self, test_client):
        """Test usuwania nieistniejącego zasobu"""
        response = test_client.delete("/movies/999999")
        assert response.status_code == 404