from db_sqlalchemy import Base
from sqlalchemy import JSON, Column, Integer, String, Float
from sqlalchemy.ext.mutable import MutableList


class Movie(Base):
	__tablename__ = "movies"

	movieId = Column(Integer, primary_key=True, index=True)
	title = Column(String)
	genres = Column(String)

	
class Link(Base):
	__tablename__ = "links"

	movieId = Column(Integer, primary_key=True)
	imdbId = Column(String)
	tmdbId = Column(String)


class Rating(Base):
	__tablename__ = "ratings"

	ratingId = Column(Integer, primary_key=True, autoincrement=True)
	userId = Column(Integer)
	movieId = Column(Integer)
	rating = Column(Float)
	timestamp = Column(Integer)

class Tag(Base):
	__tablename__ = "tags"

	tagId = Column(Integer, primary_key=True, autoincrement=True)
	userId = Column(Integer)
	movieId = Column(Integer)
	tag = Column(String)
	timestamp = Column(Integer)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    roles = Column(MutableList.as_mutable(JSON))