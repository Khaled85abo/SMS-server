from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.db_setup import get_db
from app.database.models.models import Box, Item
from app.database.schemas.schemas import BoxSchema, BoxOutSchema, BoxWithItemsAndImagesSchema

router = APIRouter()

@router.post("", response_model=BoxOutSchema)
async def create_box(box: BoxSchema, db: Session = Depends(get_db)):
    db_box = Box(**box.model_dump(exclude={"items"}))
    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return db_box

@router.get("", response_model=list[BoxWithItemsAndImagesSchema])
async def read_boxes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    boxes = db.query(Box).options(
        joinedload(Box.items).joinedload(Item.images)
    ).offset(skip).limit(limit).all()
    return boxes

@router.get("/{box_id}", response_model=BoxWithItemsAndImagesSchema)
async def read_box(box_id: int, db: Session = Depends(get_db)):
    box = db.query(Box).options(
        joinedload(Box.items).joinedload(Item.images)
    ).filter(Box.id == box_id).first()
    if box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    return box

@router.put("/{box_id}", response_model=BoxOutSchema)
async def update_box(box_id: int, box: BoxSchema, db: Session = Depends(get_db)):
    db_box = db.query(Box).filter(Box.id == box_id).first()
    if db_box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    for key, value in box.model_dump(exclude={"items"}).items():
        setattr(db_box, key, value)
    db.commit()
    db.refresh(db_box)
    return db_box

@router.delete("/{box_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_box(box_id: int, db: Session = Depends(get_db)):
    db_box = db.query(Box).filter(Box.id == box_id).first()
    if db_box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    db.delete(db_box)
    db.commit()
    return {"ok": True}