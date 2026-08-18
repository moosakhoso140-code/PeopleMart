from urllib.parse import quote_plus

from sqlalchemy import engine, create_engine

from sqlalchemy.orm import sessionmaker, declarative_base

username = "postgres"
password = quote_plus("moosa@113")  # Automatically converts '@' to '%40'
host = "localhost"
port = "5432"
db_name = "website"

SQLAlchemy_Url = (
    f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
)
engine=create_engine(SQLAlchemy_Url)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
