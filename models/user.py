from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    tokens = relationship("Token", back_populates="user")

    def __repr__(self):
        return f"<User(email='{self.email}')>"
    
class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="tokens")
    token = Column(String)
    expiration = Column(Integer)

    def __repr__(self):
        return f"<Token(token='{self.token}')>"