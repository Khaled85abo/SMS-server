from app.database.schemas.schemas import WorkSpaceSchema, WorkSpaceOutSchema, BoxSchema, BoxOutSchema, ItemSchema, ItemOutSchema, UserSchema, UserOutSchema
from sqlalchemy import Select
from sqlalchemy.orm import Session
from app.db_setup import get_db
from fastapi import Depends, APIRouter, HTTPException, status
from app.database.models.models import WorkSpace, Box, Item
# import image functions from router image_router
from app.routers.image_router import upload_image, delete_image
router = APIRouter()

# WorkSpace CRUD operations
@router.post("/workspaces", response_model=WorkSpaceOutSchema)
async def create_workspace(workspace: WorkSpaceSchema, db: Session = Depends(get_db)) -> WorkSpaceOutSchema:
    db_workspace = WorkSpace(**workspace.model_dump(exclude={"boxes"}))
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

# @router.get("/workspaces", response_model=List[WorkSpaceOutSchema])
@router.get("/workspaces")
async def read_workspaces(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    workspaces = db.query(WorkSpace).offset(skip).limit(limit).all()
    return workspaces

@router.get("/workspaces/{workspace_id}", response_model=WorkSpaceOutSchema)
async def read_workspace(workspace_id: int, db: Session = Depends(get_db)):
    workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    return workspace

@router.put("/workspaces/{workspace_id}", response_model=WorkSpaceOutSchema)
async def update_workspace(workspace_id: int, workspace: WorkSpaceSchema, db: Session = Depends(get_db)):
    db_workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
    if db_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    for key, value in workspace.dict(exclude={"boxes"}).items():
        setattr(db_workspace, key, value)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    db_workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
    if db_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    db.delete(db_workspace)
    db.commit()
    return {"ok": True}

# Box CRUD operations
@router.post("/boxes", response_model=BoxOutSchema)
async def create_box(box: BoxSchema, db: Session = Depends(get_db)):
    db_box = Box(**box.dict(exclude={"items"}))
    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return db_box

# @router.get("/boxes", response_model=List[BoxOutSchema])
@router.get("/boxes")
async def read_boxes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    boxes = db.query(Box).offset(skip).limit(limit).all()
    return boxes

@router.get("/boxes/{box_id}", response_model=BoxOutSchema)
async def read_box(box_id: int, db: Session = Depends(get_db)):
    box = db.query(Box).filter(Box.id == box_id).first()
    if box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    return box

@router.put("/boxes/{box_id}", response_model=BoxOutSchema)
async def update_box(box_id: int, box: BoxSchema, db: Session = Depends(get_db)):
    db_box = db.query(Box).filter(Box.id == box_id).first()
    if db_box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    for key, value in box.dict(exclude={"items"}).items():
        setattr(db_box, key, value)
    db.commit()
    db.refresh(db_box)
    return db_box

@router.delete("/boxes/{box_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_box(box_id: int, db: Session = Depends(get_db)):
    db_box = db.query(Box).filter(Box.id == box_id).first()
    if db_box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    db.delete(db_box)
    db.commit()
    return {"ok": True}

# Item CRUD operations
@router.post("/items", response_model=ItemOutSchema)
async def create_item(item: ItemSchema, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# @router.get("/items", response_model=List[ItemOutSchema])
@router.get("/items")
async def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@router.get("/items/{item_id}", response_model=ItemOutSchema)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/items/{item_id}", response_model=ItemOutSchema)
async def update_item(item_id: int, item: ItemSchema, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"ok": True}

# Keep the root endpoint
@router.get("/")
async def root():
    return {"message": "Hello World"}