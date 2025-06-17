"""
Pytest configuration and fixtures for auth service tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database.session import Base, get_db
# Import models so they get registered with Base.metadata
from models.user_model import User
from models.otp_model import OTP


@pytest.fixture(scope="session")
def test_client():
    """
    Create a test client for the FastAPI application.
    Set follow_redirects=False to properly test redirect responses.
    """
    with TestClient(app, follow_redirects=False) as client:
        yield client


@pytest.fixture
def test_db():
    """
    Create a test database session.
    """
    # Create an in-memory SQLite database for testing with thread check disabled
    engine = create_engine(
        "sqlite:///:memory:", 
        echo=True,  # Enable SQL logging for debugging
        connect_args={"check_same_thread": False}
    )
    
    print(f"DEBUG: Tables in metadata before create_all: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    actual_tables = inspector.get_table_names()
    print(f"DEBUG: Actual tables created in database: {actual_tables}")
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client_with_db():
    """
    Create a test client with database dependency override.
    """
    # Use a file-based SQLite database to avoid in-memory connection issues
    import tempfile
    import os
    
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    try:
        engine = create_engine(
            f"sqlite:///{db_path}", 
            echo=False,  # Disable SQL logging for cleaner output
            connect_args={"check_same_thread": False}
        )
        
        Base.metadata.create_all(bind=engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app, follow_redirects=False) as client:
            yield client
        
    finally:
        # Clean up
        app.dependency_overrides.clear()
        # Properly dispose of the engine to close all connections
        engine.dispose()
        # Remove temporary database file
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                # On Windows, sometimes the file is still locked briefly
                pass


@pytest.fixture
def mock_google_client_id():
    """
    Mock the Google Client ID for testing.
    """
    return "test_google_client_id_123456789"


@pytest.fixture
def mock_settings(mock_google_client_id):
    """
    Mock the settings module with test values.
    """
    with patch("core.config.settings") as mock_settings_obj:
        mock_settings_obj.GOOGLE_CLIENT_ID = mock_google_client_id
        mock_settings_obj.GOOGLE_CLIENT_SECRET = "test_google_client_secret"
        mock_settings_obj.SECRET_KEY = "test_secret_key_for_jwt_tokens"
        mock_settings_obj.ALGORITHM = "HS256"
        mock_settings_obj.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings_obj.REFRESH_TOKEN_EXPIRE_DAYS = 7
        yield mock_settings_obj
