from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import enum

class CarBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    plate_number: str
    # Новые поля
    brand: Optional[str] = None
    passport_data: Optional[str] = None
    organization: Optional[str] = None # Добавлено поле organization

class CarCreate(CarBase):
    pass

class CarRead(CarBase):
    id: int
    status: str
    time_in: datetime
    time_out: datetime

    class Config:
        from_attributes = True

class Status(str, enum.Enum):
    none = "none"
    in_val = "in"
    out = "out"

class HistoryBase(BaseModel):
    car_id: int
    status: Status
    date: datetime

class HistoryCreate(HistoryBase):
    pass

class HistoryRead(BaseModel):
    id: int
    car_id: int
    status: Status
    date: datetime
    car: CarRead

    class Config:
        from_attributes = True

class JournalBase(BaseModel):
    car_id: int
    plate_number: str
    fio: str
    time_in: datetime
    time_out: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organization: Optional[str] = None


class JournalCreate(JournalBase):
    pass


class JournalRead(JournalBase):
    id: int
    updated_at: Optional[datetime] = None
    organization: Optional[str] = None

    class Config:
        from_attributes = True

