import json
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker

from app.routers.auth.models import Country

load_dotenv()

ENV = os.getenv("ENV", "dev")

# Database
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)


def fill_countries_into_db():
    try:
        path_to_countries = os.getcwd() + "/app/templates/static/countries.json"
        with SessionLocal() as session:
            with open(path_to_countries) as f:
                countries_list = json.load(f)
                _insert = insert(Country).values(countries_list)
                _query = _insert.on_conflict_do_nothing(index_elements=["name"])
                session.execute(_query)
            session.commit()
    except Exception as e:
        raise e


if __name__ == "__main__":
    fill_countries_into_db()
