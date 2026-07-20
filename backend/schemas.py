"""
This module contains the Pydantic models used for request and response validation in the backend API.

The models define the structure and data types of the expected input and output for various API endpoints, ensuring that the data adheres to the specified format.
The models include fields for post creation, post retrieval, and error responses, providing a clear contract for the API consumers. By using Pydantic models, we can leverage automatic data validation, serialization, and documentation generation, making the API more robust and user-friendly. Type hints are used to specify the expected data types for each field, allowing for better code readability and maintainability. The models also include optional fields and default values where applicable, providing flexibility in the API's behavior. Overall, this module serves as a central place for defining the data structures used throughout the backend API, promoting consistency and reducing the likelihood of errors in data handling.

BaseModel is a class provided by Pydantic that serves as the base class for creating data models. It provides features such as data validation, serialization, and parsing of input data. By inheriting from BaseModel, we can define our own models with specific fields and their types, allowing us to enforce data integrity and structure in our application.

ConfigDict is a class provided by Pydantic that allows us to define configuration options for our data models. It provides a way to customize the behavior of the model, such as enabling or disabling certain features, setting default values, and specifying validation rules. By using ConfigDict, we can fine-tune the behavior of our models to suit our application's needs.

Field is a function provided by Pydantic that allows us to define additional metadata and validation rules for individual fields in our data models. It provides options such as setting default values, specifying field types, adding descriptions, and defining validation constraints. By using Field, we can enhance the functionality and usability of our models, ensuring that the data adheres to the desired format and requirements.

"""

from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    image_file: str | None
    image_path: str


class UserPrivate(UserPublic):
    email: EmailStr


# The UserUpdate model is used for updating user information. It allows for partial updates, meaning that any of the fields can be omitted if they are not being updated. The fields are defined as optional (using `str | None`), and default values are set to `None`. This means that if a field is not provided in the update request, it will not be changed in the database. The Field function is used to provide additional metadata and validation rules for each field, such as minimum and maximum lengths.
class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)


class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    """
    Base model for a blog post.

    This model defines the common fields shared by all post-related models, including the title, content, and author of the post. It serves as a foundation for other models that inherit from it, allowing for code reuse and consistency in data representation.
    """

    # Without default values, the fields are required when creating an instance of the model. The Field function is used to provide additional metadata and validation rules for each field, such as minimum and maximum lengths, descriptions, and other constraints.
    title: str = Field(
        min_length=1, max_length=100, description="The title of the blog post."
    )
    content: str = Field(min_length=1, description="The content of the blog post.")


class PostCreate(PostBase):
    """
    Model for creating a new blog post.

    This model inherits from PostBase and is used specifically for creating new posts. It includes the same fields as PostBase, but can also include additional fields or validation rules specific to the creation process if needed.
    'pass`#' means that the class does not add any new fields or methods beyond what is inherited from PostBase. It serves as a distinct model for the purpose of creating posts, allowing for clear separation of concerns and potential future extensions without modifying the base model.
    """

    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    """
    Model for the response of a blog post.

    This model inherits from PostBase and is used for returning post data in API responses. It includes all the fields from PostBase, along with an additional field for the unique identifier of the post. This allows clients to receive complete information about a post, including its ID, title, content, and author.
    """

    model_config = ConfigDict(from_attributes=True)

    # The `id` field and The `date_created` are generate by the system and not provided by the client. Both fields are essential for clients to manage and display post information effectively.

    id: int = Field(description="The unique identifier of the blog post.")
    user_id: int = Field(
        description="The unique identifier of the user who created the post."
    )
    date_posted: datetime = Field(
        description="The date and time when the blog post was created."
    )
    author: UserPublic  # The UserResponse model is used to represent the author of the post, providing detailed information about the user who created the post, including their username, email, and profile image path. This allows clients to display relevant author information alongside the post content in a user-friendly manner. This comes from the relationship defined in the Post model, which links each post to its corresponding user (author) in the database.
