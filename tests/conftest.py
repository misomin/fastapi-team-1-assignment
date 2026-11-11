from typing import Iterable

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.pool import StaticPool

from wapang.main import app
from wapang.app.users.models import User
from wapang.database.common import Base
from wapang.database.settings import DB_SETTINGS
from wapang.database.connection import get_db_session
from wapang.settings import ENV
 
@pytest.fixture(autouse=True, scope="session")
def set_test_env():
    ENV = "test"


@pytest.fixture(scope="function")
def db_engine(set_test_env) -> Iterable[sqlalchemy.Engine]:
    url = "sqlite:///:memory:"
    engine = sqlalchemy.create_engine(
        url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: sqlalchemy.Engine) -> Iterable[orm.Session]:
    with orm.Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_session: orm.Session) -> Iterable[TestClient]:

    def override_get_db_session():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        client.close()

@pytest.fixture
def user(
    client: TestClient
) -> User:
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "password123"
    }
    
    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    return User(
        id=res_json["id"],
        email=res_json["email"],
        nickname=res_json.get("nickname"),
        address=res_json.get("address"),
        phone_number=res_json.get("phone_number")
    )
    
@pytest.fixture
def token(
    client: TestClient,
    user: User
) -> dict:
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "password123"
    }
    res = client.post("/api/auth/tokens", json=req)
    res_json = res.json()
    
    return {
        "access_token": res_json["access_token"],
        "refresh_token": res_json["refresh_token"]
    }

@pytest.fixture
def access_token(
    token: dict
) -> str:
    return token["access_token"]
