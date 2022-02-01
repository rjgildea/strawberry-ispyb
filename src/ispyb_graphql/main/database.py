import configparser
import os

import ispyb.sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def get_database_url(connector: str = "mysqlconnector"):
    credentials = os.getenv("ISPYB_CREDENTIALS")
    config = configparser.RawConfigParser(allow_no_value=True)
    if not config.read(credentials):
        raise AttributeError(f"No configuration found at {credentials}")
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
