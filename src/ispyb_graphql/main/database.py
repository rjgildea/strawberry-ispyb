import configparser
import os

import ispyb.sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url():
    credentials = os.getenv("ISPYB_CREDENTIALS")
    config = configparser.RawConfigParser(allow_no_value=True)
    if not config.read(credentials):
        raise AttributeError(f"No configuration found at {credentials}")
    credentials = dict(config.items("ispyb_sqlalchemy"))
    return (
        "mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}".format(
            **credentials,
        )
    )


SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"use_pure": True}, future=True)
SessionLocal = sessionmaker(engine)
