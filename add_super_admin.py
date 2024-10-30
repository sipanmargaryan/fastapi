import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker

from app.routers.auth.models import AdminTypes, User
from app.routers.auth.utils import get_password_hash

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


def add_super_admin():
    try:
        with SessionLocal() as session:
            user_info = dict(
                first_name="Admin",
                last_name="Admin",
                email="admin@gmail.com",
                password=get_password_hash("admin"),
                active=True,
                country_id=1,
                business_phone_number="1234567890",
                admin_type=AdminTypes.superuser,
            )
            _insert = insert(User).values(**user_info)
            _query = _insert.on_conflict_do_update(
                index_elements=["email"], set_=user_info
            )
            session.execute(_query)
            session.commit()
    except Exception as e:
        raise e


if __name__ == "__main__":
    add_super_admin()
