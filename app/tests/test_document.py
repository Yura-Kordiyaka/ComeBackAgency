import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from database.settings import get_session, Base
from app.main import app
from sqlalchemy.future import select
from schemas.token import Token
from httpx import AsyncClient
from sqlalchemy.pool import NullPool
from config import settings
from io import BytesIO
import os
from docx import Document as DocxDocument
from models.document import FormattingSuggestion

DATABASE_TEST_URL = f"postgresql+asyncpg://{settings.db.DB_TEST_USER}:{settings.db.DB_TEST_PASSWORD}@{settings.db.DB_TEST_HOST}/{settings.db.DB_TEST_NAME}"

test_engine = create_async_engine(DATABASE_TEST_URL, echo=True, future=True, poolclass=NullPool)

TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
async def test_db_session():
    async with TestSessionLocal() as session:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def override_get_session(test_db_session):
    async def override_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_session


async def create_and_login_user(client, user_data):
    response = await client.post("/api/v1/user/sign_up", json=user_data)
    assert response.status_code == 201

    response = await client.post("/api/v1/user/login", data={
        "username": user_data["username"],
        "password": user_data["password"]
    })

    assert response.status_code == 200
    token_data = Token(**response.json())
    assert token_data.access_token is not None
    return token_data.access_token


@pytest.mark.asyncio
async def test_create_document(test_db_session: AsyncSession):
    user_data = {
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "hashedpassword",
        "first_name": "Test",
        "last_name": "User"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        access_token = await create_and_login_user(client, user_data)

        doc = DocxDocument()
        doc.add_paragraph("This is a test document.")
        file_path = "temp_test_document.docx"
        doc.save(file_path)

        with open(file_path, 'rb') as file:
            file_content = file.read()
        assert os.path.exists(file_path)

        file_name = os.path.basename(file_path)

        response = await client.post(
            "/api/v1/document/create",
            files={"file": (file_name, BytesIO(file_content),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 201
        document_id = response.json()["id"]

        response = await client.post(
            "/api/v1/document/apa_style_check?document_id=" + str(document_id),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 201

        response_data = response.json()

        assert "description" in response_data
        assert isinstance(response_data["description"], str)
        assert response_data["description"] != ""

        result = await test_db_session.execute(
            select(FormattingSuggestion).where(FormattingSuggestion.document_id == document_id)
        )
        formatting_suggestion = result.scalars().first()

        assert formatting_suggestion is not None
        assert formatting_suggestion.description == response_data["description"]
        os.remove(file_path)
