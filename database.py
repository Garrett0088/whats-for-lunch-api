from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load DATABASE_URL from the .env file into the process environment
load_dotenv()

# Read the connection string that was set in docker-compose.yml or .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the SQLAlchemy engine — manages the actual connection pool to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory for creating new database sessions
# autocommit=False means we control when transactions are committed
# autoflush=False means SQLAlchemy won't auto-write pending changes before queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # Opens a new database session for each request
    db = SessionLocal()
    try:
        # yield hands the session to the FastAPI route via Depends()
        yield db
    finally:
        # Always close the session when the request is done, even if an error occurred
        db.close()
