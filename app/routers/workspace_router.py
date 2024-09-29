from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.db_setup import get_db
from app.database.models.models import WorkSpace, UserWorkSpace, User
from app.database.schemas.schemas import WorkSpaceSchema, WorkSpaceOutSchema
from app.auth import get_user_id, get_user

router = APIRouter()

# @router.post("/", response_model=WorkSpaceOutSchema)
# async def create_workspace(
#     workspace: WorkSpaceSchema, 
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_user_id)
# ) -> WorkSpaceOutSchema:
#     # Create the workspace instance
#     db_workspace = WorkSpace(**workspace.model_dump(exclude={"boxes"}))
#     db.add(db_workspace)
#     db.commit()
#     db.refresh(db_workspace)
    
#     # Now the workspace ID is available
#     user_workspace = UserWorkSpace(user_id=user_id, work_space_id=db_workspace.id)
#     db.add(user_workspace)
#     db.commit()
    
#     return db_workspace

@router.post("/", response_model=WorkSpaceOutSchema)
async def create_workspace(
    workspace: WorkSpaceSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
) -> WorkSpaceOutSchema:
    # Create the workspace and associate it with the user
    db_workspace = WorkSpace(**workspace.model_dump(exclude={"boxes"}))
    db_workspace.users.append(user)
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)

    return db_workspace

# @router.get("/")
# async def read_workspaces(
#     skip: int = 0, 
#     limit: int = 100, 
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_user_id)
# ):
#     workspaces = db.query(WorkSpace).join(UserWorkSpace).filter(UserWorkSpace.user_id == user_id).offset(skip).limit(limit).all()
#     return workspaces

@router.get("/", response_model=List[WorkSpaceOutSchema])
async def read_workspaces(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
):
    workspaces = user.work_spaces[skip:skip + limit]
    return workspaces

# @router.get("/{workspace_id}", response_model=WorkSpaceOutSchema)
# async def read_workspace(
#     workspace_id: int, 
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_user_id)
# ):
#     workspace = db.query(WorkSpace).join(UserWorkSpace).filter(
#         WorkSpace.id == workspace_id,
#         UserWorkSpace.user_id == user_id
#     ).first()
#     if workspace is None:
#         raise HTTPException(status_code=404, detail="WorkSpace not found")
#     return workspace

@router.get("/{workspace_id}", response_model=WorkSpaceOutSchema)
async def read_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    workspace = db.query(WorkSpace).filter(
        WorkSpace.id == workspace_id,
        WorkSpace.users.any(id=user_id)
    ).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    return workspace

# @router.put("/{workspace_id}", response_model=WorkSpaceOutSchema)
# async def update_workspace(
#     workspace_id: int, 
#     workspace: WorkSpaceSchema, 
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_user_id)
# ):
#     db_workspace = db.query(WorkSpace).join(UserWorkSpace).filter(
#         WorkSpace.id == workspace_id,
#         UserWorkSpace.user_id == user_id
#     ).first()
#     if db_workspace is None:
#         raise HTTPException(status_code=404, detail="WorkSpace not found")
#     for key, value in workspace.dict(exclude={"boxes"}).items():
#         setattr(db_workspace, key, value)
#     db.commit()
#     db.refresh(db_workspace)
#     return db_workspace

@router.put("/{workspace_id}", response_model=WorkSpaceOutSchema)
async def update_workspace(
    workspace_id: int,
    workspace: WorkSpaceSchema,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    # First, check if the workspace exists and is associated with the user
    db_workspace = db.query(WorkSpace).join(UserWorkSpace).filter(
        WorkSpace.id == workspace_id,
        UserWorkSpace.user_id == user_id
    ).first()
    
    if db_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    
    # first way to update
    # Update the workspace attributes
    for key, value in workspace.model_dump(exclude={"boxes"}).items():
        setattr(db_workspace, key, value)
    # second way to update
    # query = update(WorkSpace).where(WorkSpace.id == workspace_id).values(name=workspace.name, description=workspace.description)
    # query = update(WorkSpace).where(WorkSpace.id == workspace_id).values(**workspace.model_dump(exclude={"boxes"}))
    # db.execute(query)
    # third way to update
    # db.query(WorkSpace).filter(WorkSpace.id == workspace_id).update(workspace.model_dump(exclude={"boxes"}))
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    db_workspace = db.query(WorkSpace).join(UserWorkSpace).filter(
        WorkSpace.id == workspace_id,
        UserWorkSpace.user_id == user_id
    ).first()
    if db_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")
    db.delete(db_workspace)
    db.commit()
    return {"ok": True}

# Delete workspace for a single user
@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    user_workspace = db.query(UserWorkSpace).filter(
        UserWorkSpace.work_space_id == workspace_id,
        UserWorkSpace.user_id == user_id
    ).first()
    if user_workspace is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found or not associated with the user")
    db.delete(user_workspace)
    db.commit()
    return {"ok": True}

# Allow deletrion only for owners
@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    db_workspace = db.query(WorkSpace).filter(
        WorkSpace.id == workspace_id,
        WorkSpace.owner_id == user_id
    ).first()
    if db_workspace is None:
        raise HTTPException(status_code=403, detail="Not authorized to delete this workspace")
    db.delete(db_workspace)
    db.commit()
    return {"ok": True}