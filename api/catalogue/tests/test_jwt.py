import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt

from api.database.app import app, SECRET_KEY, ALGORITHM  

client = TestClient(app)

# Testowe dane
TEST_USER_ADMIN = {"username": "admin", "password": "admin123"}
TEST_USER_REGULAR = {"username": "user1", "password": "password123"}
TEST_INVALID_USER = {"username": "nieistniejacy", "password": "zlehaslo"}

# Helper functions
def get_auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}

def create_test_token(username: str, roles: list = None, expired: bool = False):
    if roles is None:
        roles = []
    
    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + (timedelta(minutes=-1) if expired else timedelta(hours=1)),
        "roles": roles
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

class TestLoginEndpoint:
    """Testy dla endpointu /login"""
    
    def test_login_success_admin(self):
        """Test poprawnego logowania jako admin"""
        response = client.post("/login", json=TEST_USER_ADMIN)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Weryfikacja tokena
        token = data["access_token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == TEST_USER_ADMIN["username"]
        assert "ROLE_ADMIN" in payload.get("roles", [])
    
    def test_login_success_regular_user(self):
        """Test poprawnego logowania jako zwykły użytkownik"""
        response = client.post("/login", json=TEST_USER_REGULAR)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        # Weryfikacja tokena
        token = data["access_token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == TEST_USER_REGULAR["username"]
    
    def test_login_invalid_credentials(self):
        """Test logowania z nieprawidłowymi danymi"""
        response = client.post("/login", json=TEST_INVALID_USER)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid credentials" in data["detail"]
    
    def test_login_missing_fields(self):
        """Test logowania z brakującymi polami"""
        response = client.post("/login", json={"username": "admin"})  # Brak password
        
        assert response.status_code == 422  # Validation error
    
    def test_login_empty_password(self):
        """Test logowania z pustym hasłem"""
        response = client.post("/login", json={"username": "admin", "password": ""})
        
        assert response.status_code == 401

class TestUsersEndpoint:
    """Testy dla endpointu /users (wymaga autoryzacji ROLE_ADMIN)"""
    
    def test_create_user_success_with_admin_token(self):
        """Test tworzenia użytkownika z poprawnym tokenem admina"""
        # 1. Zaloguj się jako admin aby uzyskać token
        login_response = client.post("/login", json=TEST_USER_ADMIN)
        admin_token = login_response.json()["access_token"]
        
        # 2. Utwórz nowego użytkownika
        new_user = {
            "username": "testuser_" + datetime.now().strftime("%H%M%S"),
            "password": "testpassword123",
            "roles": ["ROLE_USER"]
        }
        
        response = client.post(
            "/users",
            json=new_user,
            headers=get_auth_header(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User created successfully"
        assert data["username"] == new_user["username"]
        assert data["roles"] == new_user["roles"]
        assert "created_by" in data
    
    def test_create_user_duplicate_username(self):
        """Test tworzenia użytkownika z istniejącą nazwą"""
        login_response = client.post("/login", json=TEST_USER_ADMIN)
        admin_token = login_response.json()["access_token"]
        
        response = client.post(
            "/users",
            json={"username": "admin", "password": "newpassword123", "roles": []},
            headers=get_auth_header(admin_token)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Username already registered" in data["detail"]
    
    def test_create_user_without_admin_role(self):
        """Test tworzenia użytkownika bez uprawnień ROLE_ADMIN"""
        # Utwórz token bez roli ADMIN
        non_admin_token = create_test_token("regular_user", roles=["ROLE_USER"])
        
        new_user = {
            "username": "unauthorized_user",
            "password": "test123",
            "roles": ["ROLE_USER"]
        }
        
        response = client.post(
            "/users",
            json=new_user,
            headers=get_auth_header(non_admin_token)
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Insufficient permissions" in data["detail"]
    
    def test_create_user_without_token(self):
        """Test tworzenia użytkownika bez tokena"""
        new_user = {
            "username": "testuser",
            "password": "test123",
            "roles": []
        }
        
        response = client.post("/users", json=new_user)
        
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing token
        data = response.json()
        assert "detail" in data
    
    def test_create_user_with_invalid_token(self):
        """Test tworzenia użytkownika z nieprawidłowym tokenem"""
        response = client.post(
            "/users",
            json={"username": "test", "password": "test", "roles": []},
            headers=get_auth_header("invalid_token_here")
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_create_user_with_expired_token(self):
        """Test tworzenia użytkownika z wygasłym tokenem"""
        expired_token = create_test_token("admin", roles=["ROLE_ADMIN"], expired=True)
        
        response = client.post(
            "/users",
            json={"username": "test", "password": "test", "roles": []},
            headers=get_auth_header(expired_token)
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower()

class TestUserDetailsEndpoint:
    """Testy dla endpointu /user_details"""
    
    def test_user_details_success(self):
        """Test pobierania danych użytkownika z poprawnym tokenem"""
        # 1. Zaloguj się aby uzyskać token
        login_response = client.post("/login", json=TEST_USER_ADMIN)
        token = login_response.json()["access_token"]
        
        # 2. Pobierz dane użytkownika
        response = client.get(
            "/user_details",
            headers=get_auth_header(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Sprawdź strukturę odpowiedzi
        assert "username" in data
        assert data["username"] == TEST_USER_ADMIN["username"]
        assert "roles" in data
        assert isinstance(data["roles"], list)
        assert "issued_at" in data
        assert "expires_at" in data
        
        # Sprawdź czy ROLE_ADMIN jest w rolach
        assert "ROLE_ADMIN" in data["roles"]
    
    def test_user_details_without_token(self):
        """Test pobierania danych użytkownika bez tokena"""
        response = client.get("/user_details")
        
        assert response.status_code == 403  # HTTPBearer zwraca 403 dla braku tokena
        data = response.json()
        assert "detail" in data
    
    def test_user_details_with_invalid_token(self):
        """Test pobierania danych użytkownika z nieprawidłowym tokenem"""
        response = client.get(
            "/user_details",
            headers=get_auth_header("nieprawidlowy.token.123")
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_user_details_with_expired_token(self):
        """Test pobierania danych użytkownika z wygasłym tokenem"""
        expired_token = create_test_token("admin", roles=["ROLE_ADMIN"], expired=True)
        
        response = client.get(
            "/user_details",
            headers=get_auth_header(expired_token)
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower()
    
    def test_user_details_regular_user_token(self):
        """Test pobierania danych użytkownika z tokenem zwykłego użytkownika"""
        # Utwórz token dla zwykłego użytkownika
        regular_token = create_test_token("regular_user", roles=["ROLE_USER"])
        
        response = client.get(
            "/user_details",
            headers=get_auth_header(regular_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "regular_user"
        assert data["roles"] == ["ROLE_USER"]
    
    def test_user_details_token_without_roles(self):
        """Test pobierania danych użytkownika z tokenem bez ról"""
        token_no_roles = create_test_token("user_no_roles", roles=[])
        
        response = client.get(
            "/user_details",
            headers=get_auth_header(token_no_roles)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user_no_roles"
        assert data["roles"] == []

# Testy dla innych endpointów (jeśli chcesz)
class TestOtherEndpoints:
    """Testy dla pozostałych endpointów"""
    
    def test_get_movies(self):
        """Test endpointu /movies"""
        response = client.get("/movies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_links(self):
        """Test endpointu /links"""
        response = client.get("/links")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_ratings(self):
        """Test endpointu /ratings"""
        response = client.get("/ratings")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_tags(self):
        """Test endpointu /tags"""
        response = client.get("/tags")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_root_endpoint(self):
        """Test endpointu głównego"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}