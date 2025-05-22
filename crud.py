from datetime import datetime
from sqlalchemy.orm import Session
import models
from models import Status
from sqlalchemy import desc, and_
from typing import Optional


def add_car(db: Session, last_name: str, first_name: str, middle_name: str, plate_number: str, brand: str = None, passport_data: str = None, organization: str = None):
    new_car = models.Car(
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        plate_number=plate_number,
        # Новые поля
        brand=brand,
        passport_data=passport_data,
        organization=organization,
        status=Status.none,
        time_in=datetime(1970, 1, 1),
        time_out=datetime(1970, 1, 1)
    )
    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return new_car

def delete_car(db: Session, car_id: int):
    car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if car:
        db.delete(car)
        db.commit()
        return car
    return None

def delete_car_by_plate(db: Session, plate_number: str):
    """Deletes a car by its plate number."""
    car = db.query(models.Car).filter(models.Car.plate_number == plate_number).first()
    if car:
        db.delete(car)
        db.commit()
        return car
    return None


def get_all_cars(db: Session):
    return db.query(models.Car).all()

def get_car_by_id(db: Session, car_id: int):
    return db.query(models.Car).filter(models.Car.id == car_id).first()

def get_all_history(db: Session):
    return db.query(models.History).all()

def generate_report(db: Session, start_date: datetime, end_date: datetime = None):
    if end_date is None:
        end_date = datetime.utcnow()

    history_records = db.query(models.History).filter(models.History.date >= start_date, models.History.date <= end_date) \
        .join(models.Car) \
        .all()

    report = []
    for record in history_records:
        car = record.car
        status_text = ""
        if record.status.value == "in":
            status_text = "Заехал"
        elif record.status.value == "out":
            status_text = "Выехал"
        else:
            status_text = None

        report.append({
            "car_id": car.id,
            "plate_number": car.plate_number,
            "fio": f"{car.last_name} {car.first_name} {car.middle_name}",
            "status": status_text,
            "date": record.date.strftime("%H:%M:%S %d.%m.%Y"),
            "current_status": car.status.value,
            "time_in": car.time_in.strftime("%H:%M:%S %d.%m.%Y") if car.time_in else None,
            "time_out": car.time_out.strftime("%H:%M:%S %d.%m.%Y",) if car.time_out else None,
            # Добавляем новые поля в отчет (если нужно)
            "brand": car.brand,
            "passport_data": car.passport_data,
            "organization": car.organization,
        })

    return report

def history_count(db: Session, count: int):
    history_records = (
        db.query(models.History)
        .order_by(desc(models.History.date))
        .limit(count)
        .all()
    )

    result = []
    for record in history_records:
        car = record.car
        status = ""
        if record.status.value == "in":
            status = "Заехал"
        elif record.status.value == "out":
            status = "Выехал"
        else:
            status = None
        result.append({
            "id": record.id,
            "car_id": car.id,
            "status": status,
            "date": record.date.isoformat(),
            "car": {
                "last_name": car.last_name,
                "first_name": car.first_name,
                "middle_name": car.middle_name,
                "plate_number": car.plate_number,
                "id": car.id,
                "status": car.status.value,
                "time_in": car.time_in.isoformat() if car.time_in else None,
                "time_out": car.time_out.isoformat() if car.time_out else None,
                # Добавляем новые поля в результат (если нужно)
                "brand": car.brand,
                "passport_data": car.passport_data,
                "organization": car.organization,
            }
        })

    return result

def create_journal_entry(db: Session, car: models.Car):
    """Creates a new journal entry when a car enters."""
    journal_entry = models.Journal(
        car_id=car.id,
        plate_number=car.plate_number,
        fio=f"{car.last_name} {car.first_name} {car.middle_name}",
        time_in=car.time_in,
        organization=car.organization  # Добавляем организацию
    )
    db.add(journal_entry)
    db.commit()
    db.refresh(journal_entry)
    return journal_entry


def update_journal_entry_on_exit(db: Session, car: models.Car):
    """Updates the journal entry with the exit time when a car leaves, only updating the *latest* entry."""
    journal_entry = db.query(models.Journal).filter(models.Journal.car_id == car.id, models.Journal.time_out == None).order_by(desc(models.Journal.time_in)).first()
    if journal_entry:
        journal_entry.time_out = car.time_out
        db.commit()
        db.refresh(journal_entry)
    return journal_entry

def get_journal_entries(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    """
    Retrieves journal entries based on the provided date range, using the updated_at field.

    Args:
        db: The database session.
        start_date: The start date for filtering (optional).
        end_date: The end date for filtering (optional).  Defaults to now.

    Returns:
        A list of journal entries.
    """
    query = db.query(models.Journal)

    if end_date is None:
        end_date = datetime.utcnow()

    if start_date:
        query = query.filter(and_(models.Journal.updated_at >= start_date, models.Journal.updated_at <= end_date))
    else:
        query = query.filter(models.Journal.updated_at <= end_date)  # all entries up to end_date

    return query.all()