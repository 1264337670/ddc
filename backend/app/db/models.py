from datetime import date, datetime
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Column  # 用 Column ！
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(64), nullable=False)
    avatar = Column(Text, nullable=True)
    xhs_url = Column(String(255), nullable=True)
    email = Column(String(120), unique=True, nullable=True)
    gender = Column(String(16), nullable=True)
    phone = Column(String(32), unique=True, nullable=True)
    signature = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TreePost(Base):
    __tablename__ = "tree_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tree_slug = Column(String(32), nullable=False)
    author_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(16), nullable=False, default="approved")
    hug_count = Column(Integer, nullable=False, default=0)
    sense_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TreeComment(Base):
    __tablename__ = "tree_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, ForeignKey("tree_posts.id"), nullable=False)
    author_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    content = Column(String(500), nullable=False)
    status = Column(String(16), nullable=False, default="approved")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class TreePostReaction(Base):
    __tablename__ = "tree_post_reactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, ForeignKey("tree_posts.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reaction_type = Column(String(16), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Mentor(Base):
    __tablename__ = "mentors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    intro = Column(String(255), nullable=False)
    location = Column(String(64), nullable=False)
    avatar = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MentorAppointment(Base):
    __tablename__ = "mentor_appointments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    mentor_id = Column(BigInteger, ForeignKey("mentors.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    time_slot = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="booked")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MentorSchedule(Base):
    __tablename__ = "mentor_schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    mentor_id = Column(BigInteger, ForeignKey("mentors.id"), nullable=False)
    schedule_date = Column(Date, nullable=False)
    time_slot = Column(String(32), nullable=False)
    capacity = Column(Integer, nullable=False, default=5)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserPost(Base):
    __tablename__ = "user_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    post_uid = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(64), nullable=False)
    posted_at = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)