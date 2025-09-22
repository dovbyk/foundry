#Establishes the SQLAlchemy async engine and session management for the application database (SQLite for development).


from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Use SQLite for local development
DATABASE_URL = "sqlite+aiosqlite:///./foundry.db"

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session maker
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Base class for our database models
Base = declarative_base()
