from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Force SQLite for local testing if Postgres/Docker service is not present
db_url = settings.database_url
if "postgresql" in db_url or "db:5432" in db_url:
    db_url = "sqlite:///./ledger.db"

engine = create_engine(
    db_url, 
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Automatically create tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine, checkfirst=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()