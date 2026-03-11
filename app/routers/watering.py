from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PlantOut, WateringRecordOut
from app.models import User
from app.auth import get_current_user
from app import crud

router = APIRouter(tags=["watering"])


@router.post("/api/plants/{plant_id}/water", response_model=WateringRecordOut, status_code=201)
def water_plant(plant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """浇水打卡"""
    plant = crud.get_plant(db, plant_id, user_id=current_user.id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return crud.water_plant(db, plant)


@router.get("/api/reminders", response_model=list[PlantOut])
def get_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取今天需要浇水的植物（含逾期）"""
    return crud.get_reminders(db, user_id=current_user.id)


@router.get("/api/plants/{plant_id}/records", response_model=list[WateringRecordOut])
def get_watering_records(plant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """查看浇水历史"""
    plant = crud.get_plant(db, plant_id, user_id=current_user.id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return crud.get_watering_records(db, plant_id)
