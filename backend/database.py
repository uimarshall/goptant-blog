from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },  # SQLite specific argument to allow multiple threads to access the database simultaneously. This is necessary because SQLite has a default behavior of allowing only one thread to access the database at a time, which can cause issues in a multi-threaded environment like FastAPI.
)

# The sessionmaker function is used to create a new session factory, which is a class that can be used to create new Session objects. The autocommit and autoflush parameters are set to False to ensure that changes to the database are not automatically committed or flushed, giving the developer more control over when changes are saved to the database.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# The DeclarativeBase class is a base class for all ORM models in SQLAlchemy. It provides a way to define the structure of the database tables and their relationships using Python classes. By inheriting from DeclarativeBase, you can define your own ORM models that map to database tables.
class Base(DeclarativeBase):
    pass


# The get_db function is a dependency that provides a database session to the route handlers. It uses a context manager (the with statement) to ensure that the session is properly closed after use, even if an exception occurs. The yield statement allows the function to return the session to the caller while still maintaining control over the session's lifecycle. This is important for managing database connections efficiently and preventing resource leaks.
def get_db():
    with SessionLocal() as db:
        yield db
