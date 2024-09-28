from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db_setup import get_db
from app.database.models.models import WorkSpace
from app.database.schemas.schemas import WorkSpaceSchema, WorkSpaceOutSchema

router = APIRouter()

@router.post("/", response_model=WorkSpaceOutSchema)
async def create_workspace(workspace: WorkSpaceSchema, db: Session = Depends(get_db)) -> WorkSpaceOutSchema:
    db_workspace = WorkSpace(**workspace.model_dump(exclude={"boxes"}))
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@router.get("/")
async def read_workspaces(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    workspaces = db.query(WorkSpace).offset(skip).limit(limit).all()
    return workspaces

@router.get("/{workspace_id}", response_model=WorkSpaceOutSchema)
async def read_workspace(workspace_id: int, db: Session = Depends(get_db)):
    workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    return workspace

@router.put("/{workspace_id}", response_model=WorkSpaceOutSchema)
async def update_workspace(workspace_id: int, workspace: WorkSpaceSchema, db: Session = Depends(get_db)):
    db_workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
    if db_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    for key, value in workspace.dict(exclude={"boxes"}).items():
        setattr(db_workspace, key, value)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    db_workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
    if db_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    db.delete(db_workspace)
    db.commit()
    return {"ok": True}