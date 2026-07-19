"""
database.py
------------
Configuration de la connexion SQLite et gestion des sessions SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
 
SQLALCHEMY_DATABASE_URL = "sqlite:///./shop.db"
 
# check_same_thread=False est nécessaire pour SQLite avec FastAPI (accès multi-thread)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
Base = declarative_base()
 
 
def get_db():
    """Dependency FastAPI : fournit une session DB par requête et la ferme proprement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 