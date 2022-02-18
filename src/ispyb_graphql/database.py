from __future__ import annotations

import configparser
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def get_database_url(connector: str = "mysqlconnector"):
    credentials_filename = os.getenv("ISPYB_CREDENTIALS")
    assert credentials_filename, "ISPYB_CREDENTIALS environment variable not set"
    config = configparser.RawConfigParser(allow_no_value=True)
    if not config.read(credentials_filename):
        raise AttributeError(f"No configuration found at {credentials_filename}")
    credentials = dict(config.items("ispyb_sqlalchemy"))
    return (
        f"mysql+{connector}"
        "://{username}:{password}@{host}:{port}/{database}".format(
            **credentials,
        )
    )


SQLALCHEMY_DATABASE_URL = get_database_url(connector="asyncmy")

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession)


async def get_db_session():
    return SessionLocal()
