"""The create_engine function is used to create a new SQLAlchemy engine, which is the starting point for any SQLAlchemy application. It represents the core interface to the database and provides a way to connect to the database, execute SQL statements, and manage transactions. The engine is responsible for managing the connection pool and handling database connections efficiently."""

# from sqlalchemy import create_engine
# Using the async version of create_engine to support asynchronous database operations. This allows for non-blocking database interactions, which can improve the performance and responsiveness of the application, especially in scenarios with high concurrency or I/O-bound tasks. The I/O-bound tasks can include database queries, network requests, or file operations that may take time to complete. By using asynchronous operations, the application can continue to handle other requests while waiting for the I/O-bound tasks to finish, leading to better resource utilization and improved user experience.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },  # SQLite specific argument to allow multiple threads to access the database simultaneously. This is necessary because SQLite has a default behavior of allowing only one thread to access the database at a time, which can cause issues in a multi-threaded environment like FastAPI.
)

# The sessionmaker function is used to create a new session factory, which is a class that can be used to create new Session objects. The autocommit and autoflush parameters are set to False to ensure that changes to the database are not automatically committed or flushed, giving the developer more control over when changes are saved to the database.

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# The DeclarativeBase class is a base class for all ORM models in SQLAlchemy. It provides a way to define the structure of the database tables and their relationships using Python classes. By inheriting from DeclarativeBase, you can define your own ORM models that map to database tables.
class Base(DeclarativeBase):
    pass


# The get_db function is a dependency that provides a database session to the route handlers. It uses a context manager (the with statement) to ensure that the session is properly closed after use, even if an exception occurs. The yield statement allows the function to return the session to the caller while still maintaining control over the session's lifecycle. This is important for managing database connections efficiently and preventing resource leaks.
# def get_db():
#     with SessionLocal() as db:
#         yield db


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
