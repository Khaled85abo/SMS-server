from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, DateTime, func, Enum, UniqueConstraint
from datetime import datetime
from app.database.models.base_model import Base


class ItemImage(Base):
    __tablename__ = "item_image"

    url: Mapped[str] = mapped_column(nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE", onupdate="CASCADE"))
    item: Mapped["Item"] = relationship(back_populates="images")
    def __repr__(self):
        return f"<Item_image={self.url}>"

class Item(Base):
    __tablename__ = "item"

    name: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Enum("removed", "borrowed", "Exist",name="status"),  default="Exist")
    image: Mapped[str] = mapped_column(String, nullable=True)
    box_id: Mapped[int] = mapped_column(ForeignKey("box.id", ondelete="CASCADE", onupdate="CASCADE"))
    box: Mapped["Box"] = relationship(back_populates="items")
    images: Mapped[list["ItemImage"]] = relationship(back_populates="item", cascade="all, delete")
    def __repr__(self):
        return f"<Item={self.name}>"
    
class Box(Base):
    __tablename__ = "box"

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    work_space_id: Mapped[int] = mapped_column(ForeignKey("work_space.id", ondelete="CASCADE", onupdate="CASCADE"))
    items: Mapped[list["Item"]] = relationship(back_populates="box", cascade="all, delete")
    work_space: Mapped["WorkSpace"] = relationship(back_populates="boxes")
    def __repr__(self):
        return f"<Box={self.name}>"
    
class WorkSpace(Base):
    __tablename__ = "work_space"

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    boxes: Mapped[list["Box"]] = relationship(back_populates="work_space", cascade="all, delete")
    share_code: Mapped[str] = mapped_column(nullable=True)
    users: Mapped[list["User"]] = relationship(secondary="user_work_space", back_populates="work_spaces")
    resources: Mapped[list["Resource"]] = relationship(back_populates="work_space", cascade="all, delete")

    def __repr__(self):
        return f"<Work_space={self.name}>"

class User(Base):
    __tablename__ = "user"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    email_verified: Mapped[bool] = mapped_column( default=False)
    access_token: Mapped[str] = mapped_column(nullable=True)
    token_type: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=False)
    resources: Mapped[list["Resource"]] = relationship(back_populates="user", cascade="all, delete")
    work_spaces: Mapped[list["WorkSpace"]] = relationship(secondary="user_work_space", back_populates="users")

    def __repr__(self):
        return f"<User={self.username}>"
    

class UserWorkSpace(Base):
    __tablename__ = "user_work_space"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    work_space_id: Mapped[int] = mapped_column(ForeignKey("work_space.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(Enum("owner", "admin", "viewer", name="role"), default="owner")
    __table_args__ = (
        UniqueConstraint("user_id", "work_space_id"),
    )
    def __repr__(self):
        return f"<User_work_space={self.user_id}>"

class Resource(Base):
    __tablename__ = "resource"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    work_space_id: Mapped[int] = mapped_column(ForeignKey("work_space.id", ondelete="CASCADE", onupdate="CASCADE"))

    work_space: Mapped["WorkSpace"] = relationship(back_populates="resources", foreign_keys=[work_space_id])
    user: Mapped["User"] = relationship(back_populates="resources", foreign_keys=[user_id]) 

    def __repr__(self):
        return f"<Resource={self.name}>"
