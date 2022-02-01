import ispyb.sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = ispyb.sqlalchemy.url()

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"use_pure": True})
SessionLocal = sessionmaker(bind=engine)
