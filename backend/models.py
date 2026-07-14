from __future__ import annotations

from datetime import UTC, datetime

from database import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


# The id attribute is an integer that serves as the primary key for the User table. It is automatically generated and indexed for efficient lookups. Primary keys are automatically indexed, and indexing them allows for faster searches and retrievals of records based on their primary key values. "Mapped" is a type hint provided by SQLAlchemy to indicate that this attribute is mapped to a database column.
class User(Base):
    __tablename__ = "users"

    # The User class represents a user in the database. It has the following attributes:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )
    # The posts attribute establishes a one-to-many relationship between the User and Post models. It indicates that a user can have multiple posts associated with them. The back_populates parameter specifies the corresponding attribute in the Post model that refers back to the User model, allowing for bidirectional access between the two models.

    # The cascade parameter is set to "all, delete-orphan", which means that when a user is deleted, all their associated posts will also be deleted. Additionally, if a post is removed from the user's posts collection, it will be automatically deleted from the database as well. This ensures that there are no orphaned posts (posts that has no user) left in the database when a user is removed or when a post is disassociated from a user.

    posts: Mapped[list[Post]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

    # The image_path property is a computed attribute that returns the path to the user's profile picture. If the user has uploaded a custom image, it returns the path to that image; otherwise, it returns the path to a default profile picture. This property is useful for rendering user profile images in templates or APIs without exposing the underlying file storage details.
    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/user-profile-placeholder.webp"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # The author attribute establishes a many-to-one relationship between the Post and User models. It indicates that each post is associated with a single user (the author). The back_populates parameter specifies the corresponding attribute in the User model that refers back to the Post model, allowing for bidirectional access between the two models.
    author: Mapped[User] = relationship(back_populates="posts")
