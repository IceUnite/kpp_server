from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import crud, schemas, models
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from models import Status
from typing import Optional, List
from config import pass_hash

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)
app = FastAPI()



def encrypt(st):
    encrypted_chars = [chr(ord(char) ^ 256) for char in st]
    encrypted_string = "".join(encrypted_chars)
    return encrypted_string



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Добавление новой машины
@app.post("/add_car")
def add_car(last_name: str, first_name: str, middle_name: str, plate_number: str, password: str,
            brand: Optional[str] = None, passport_data: Optional[str] = None, organization: Optional[str] = None,
            db: Session = Depends(get_db)):
    if get_string_hash(password) in pass_hash:
        new_car = crud.add_car(db, last_name, first_name, middle_name, plate_number, brand, passport_data, organization)
        return {"message": "Car added successfully", "car": new_car}
    else:
        raise HTTPException(status_code=422, detail="Incorrect password")

# Удаление машины по ID
@app.delete("/delete_car/{car_id}")
def delete_car(car_id: int, password:str, db: Session = Depends(get_db)):
    if get_string_hash(password) in pass_hash:
        car = crud.delete_car(db, car_id)
        if car is None:
            raise HTTPException(status_code=404, detail="Car not found")
        return {"message": "Car deleted successfully", "car": car}
    else:
        raise HTTPException(status_code=422, detail="Incorrect password")


@app.delete("/delete_car_by_plate/{plate_number}")
def delete_car_by_plate(plate_number: str, password:str, db: Session = Depends(get_db)):
    if get_string_hash(password) in pass_hash:
        car = crud.delete_car_by_plate(db, plate_number)
        if car is None:
            raise HTTPException(status_code=404, detail="Car not found")
        return {"message": "Car deleted successfully", "car": car}
    else:
        raise HTTPException(status_code=422, detail="Incorrect password")

# Просмотр всех машин
@app.get("/cars", response_model=list[schemas.CarRead])
def read_cars(id: int = None, db: Session = Depends(get_db)):
    if id:
        car = crud.get_car_by_id(db, id)
        if car:
            return [car]
        else:
            raise HTTPException(status_code=404, detail="Car not found")
    else:
        cars = crud.get_all_cars(db)
        return cars

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    history_records = crud.get_all_history(db)

    if not history_records:
        return []

    result = []
    for record in history_records:
        car = db.query(models.Car).filter(models.Car.id == record.car_id).first()
        if car:
            record_with_car = schemas.HistoryRead(
                **record.__dict__,
                car=schemas.CarRead(**car.__dict__)
            )
            result.append(record_with_car)

    return result

# Генерация отчета
@app.get("/generate_report", response_model=dict)
def generate_report(start_date: datetime, end_date: datetime = None, db: Session = Depends(get_db)):
    report = crud.generate_report(db, start_date, end_date)
    if not report:
        raise HTTPException(status_code=404, detail="Отсутствуют записи за выбранный период")
    return {"report": report}


@app.post("/admit_car/{car_id}")
def admit_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    car.status = Status.in_val
    car.time_in = datetime.utcnow()
    db.commit()

    history_entry = models.History(
        car_id=car.id,
        status=Status.in_val,
        date=datetime.utcnow()
    )
    db.add(history_entry)
    db.commit()

    # Create Journal entry
    crud.create_journal_entry(db, car)

    return {"message": "Car admitted successfully", "car_id": car.id, "time_in": car.time_in}


@app.post("/exit_car/{car_id}")
def exit_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    car.status = Status.out
    car.time_out = datetime.utcnow()
    db.commit()

    history_entry = models.History(
        car_id=car.id,
        status=Status.out,
        date=datetime.utcnow()
    )
    db.add(history_entry)
    db.commit()

    # Update journal entry
    crud.update_journal_entry_on_exit(db, car)

    return {"message": "Car exited successfully", "car_id": car.id, "time_out": car.time_out}

# Новый метод для поиска машины по номеру
@app.get("/car/{plate_number}", response_model=schemas.CarRead)
def read_car_by_plate(plate_number: str, db: Session = Depends(get_db)):
    car = db.query(models.Car).filter(models.Car.plate_number == plate_number).first()
    if car:
        return car
    else:
        raise HTTPException(status_code=404, detail="Car not found")

@app.get("/history_count/{count}")
def get_history_count(count: int, db: Session = Depends(get_db)):
    history_records = crud.history_count(db, count)
    return history_records

@app.get("/journal", response_model=List[schemas.JournalRead])
def read_journal_entries(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves journal entries based on the provided date range.

    Args:
        start_date: The start date for filtering (optional).
        end_date: The end date for filtering (optional). Defaults to now.

    Returns:
        A list of journal entries.
    """
    journal_entries = crud.get_journal_entries(db, start_date, end_date)
    return journal_entries


import hashlib
def get_string_hash(input_string: str) -> str:
    """
    Вычисляет SHA-256 хеш строки.

    Args:
        input_string: Входная строка.

    Returns:
        Строка, представляющая собой SHA-256 хеш входной строки в шестнадцатеричном формате.
    """
    # Преобразуем строку в байты, так как hashlib работает с байтами.
    encoded_string = input_string.encode('utf-8')

    # Создаем объект хеширования SHA-256.
    sha256_hash = hashlib.sha256()

    # Обновляем объект хеширования байтами строки.
    sha256_hash.update(encoded_string)

    # Получаем шестнадцатеричное представление хеша.
    hex_hash = sha256_hash.hexdigest()

    return hex_hash

import pandas as pd
import openpyxl
# Load the Excel file
# Load the Excel file
"""excel_file = "database.xlsx"
try:
    df = pd.read_excel(excel_file)
except FileNotFoundError:
    print(f"Error: File '{excel_file}' not found.")
    exit()
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit()

# Validate the column names
required_columns = ["Марка", "Номер", "Фамилия", "Имя", "Отчество", "Доп. данные", "Организация"]
if not all(col in df.columns for col in required_columns):
    print(f"Error: Required columns not found in Excel.  Expected columns: {', '.join(required_columns)}")
    print(f"Found columns: {', '.join(df.columns)}")
    exit()

# Create a session
db: Session = SessionLocal()
try:
    # Iterate through the rows of the DataFrame and insert into the database
    for index, row in df.iterrows():
        # Extract data from the Excel row
        brand = row["Марка"]
        plate_number = row["Номер"]
        last_name = row["Фамилия"]
        first_name = row["Имя"]
        middle_name = str(row["Отчество"]).strip()  # <--- Convert to string and remove leading/trailing spaces
        passport_data = row["Доп. данные"]
        organization = row["Организация"]

        # Check if middle_name is empty after stripping
        if not middle_name:
            middle_name = None  # Set to None if empty

        # Add car to the database using the add_car function
        crud.add_car(
            db,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            plate_number=plate_number,
            brand=brand,
            passport_data=passport_data,
            organization=organization,
        )

    db.commit()
    print("Data imported successfully!")

except Exception as e:
    db.rollback()
    print(f"An error occurred: {e}")
finally:
    db.close()
    """



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    pass

