# pytest configuration file

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import ispyb_graphql


@pytest.fixture()
async def testdb(monkeypatch):
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "db.cfg"))
    if not os.path.exists(config_file):
        pytest.skip(
            "No configuration file for test database found. Skipping database tests"
        )
    monkeypatch.setenv("ISPYB_CREDENTIALS", config_file)

    SQLALCHEMY_DATABASE_URL = ispyb_graphql.database.get_database_url(
        connector="asyncmy"
    )
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession)
    monkeypatch.setattr(ispyb_graphql.database, "SessionLocal", SessionLocal)
    return config_file
