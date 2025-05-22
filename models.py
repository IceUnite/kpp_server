# models.py
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Status(enum.Enum):
    none = "none"
    in_val = "in"
    out = "out"

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, index=True)
    first_name = Column(String)
    middle_name = Column(String)
    plate_number = Column(String, index=True)
    # Новые поля
    brand = Column(String, index=True, nullable=True) # Марка машины
    passport_data = Column(String, nullable=True) # Паспортные данные
    organization = Column(String, nullable=True) # Организация
    status = Column(Enum(Status), default=Status.none)
    time_in = Column(DateTime)
    time_out = Column(DateTime)
    histories = relationship("History", back_populates="car")

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    status = Column(Enum(Status))
    date = Column(DateTime)
    car = relationship("Car", back_populates="histories")

class Journal(Base):  # Новая таблица
    __tablename__ = "journal"
    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))  # Foreign key to the car
    plate_number = Column(String)  # Duplicate for easy access
    fio = Column(String)  # Combined full name
    time_in = Column(DateTime)
    time_out = Column(DateTime, nullable=True)  # Can be null if car hasn't left yet
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    organization = Column(String, nullable=True)  # Add organization field