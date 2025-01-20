# Define los modelos de base de datos

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    hashed_password = Column(String)

class Datasets(Base):
    __tablename__ = 'datasets'
    id_dataset = Column(Integer,primary_key=True,index=True)
    dataset_name = Column(String)
    n_rows = Column(Integer)
    n_columns = Column(Integer)
    selected = Column(Boolean)