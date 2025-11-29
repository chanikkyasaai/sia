from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db_session
from app.db.models.reminders import Reminder
from app.schema.reminders import ReminderCreate, ReminderResponse

router = APIRouter()

@router.post("/", response_model=ReminderResponse)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db_session)):
    new_reminder = Reminder(**reminder.model_dump())
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    return new_reminder

@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: int, db: Session = Depends(get_db_session)):
    return db.query(Reminder).filter(Reminder.id == reminder_id).first()

@router.get("/", response_model=list[ReminderResponse])
def get_all_reminders(db: Session = Depends(get_db_session)):
    return db.query(Reminder).all()

@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(reminder_id: int, reminder: ReminderCreate, db: Session = Depends(get_db_session)):
    existing_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    for key, value in reminder.model_dump().items():
        setattr(existing_reminder, key, value)
    db.commit()
    db.refresh(existing_reminder)
    return existing_reminder

@router.delete("/{reminder_id}", response_model=dict)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db_session)):
    existing_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    db.delete(existing_reminder)
    db.commit()
    return {"message": "Reminder deleted successfully"}