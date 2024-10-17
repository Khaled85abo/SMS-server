from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.db_setup import get_db
from app.database.models.models import WorkSpace, UserWorkSpace, User, Box
from app.database.schemas.schemas import WorkSpaceSchema, WorkSpaceOutSchema
from app.auth import get_user_id, get_user

router = APIRouter()

def get_workspaces_with_roles(db: Session, user_id: int, workspace_id: Optional[int] = None, skip: int = 0, limit: int = 100, include_items: bool = False):
    query = db.query(WorkSpace, UserWorkSpace.role).join(
        UserWorkSpace, 
        (UserWorkSpace.work_space_id == WorkSpace.id) & (UserWorkSpace.user_id == user_id)
    )

    if include_items:
        query = query.options(joinedload(WorkSpace.boxes).joinedload(Box.items))
    else:
        query = query.options(joinedload(WorkSpace.boxes))

    if workspace_id is not None:
        query = query.filter(WorkSpace.id == workspace_id)
    else:
        query = query.offset(skip).limit(limit)

    return query.all()


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

# @router.post("/", response_model=WorkSpaceOutSchema)
@router.post("/")
async def create_workspace(
    workspace: WorkSpaceSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
) :
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
async def get_all_workspaces(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
):
    try:
        # Query workspaces with user roles and eagerly load boxes, items, and resources
        workspaces_with_roles = db.query(WorkSpace, UserWorkSpace.role).join(
            UserWorkSpace, 
            (UserWorkSpace.work_space_id == WorkSpace.id) & (UserWorkSpace.user_id == user.id)
        ).options(
            joinedload(WorkSpace.boxes).joinedload(Box.items),
            joinedload(WorkSpace.resources)
        ).offset(skip).limit(limit).all()

        # Prepare the response
        result = []
        for workspace, role in workspaces_with_roles:
            workspace_dict = workspace.__dict__
            workspace_dict['role'] = role
            workspace_dict['boxes'] = [
                {**box.__dict__, 'items': [item.__dict__ for item in box.items]}
                for box in workspace.boxes
            ]
            workspace_dict['resources'] = [resource.__dict__ for resource in workspace.resources]
            result.append(WorkSpaceOutSchema(**workspace_dict))

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
async def get_single_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    # Query the workspace and user role in a single query
    workspace_with_role = db.query(WorkSpace, UserWorkSpace.role).join(
        UserWorkSpace,
        (UserWorkSpace.work_space_id == WorkSpace.id) & (UserWorkSpace.user_id == user_id)
    ).options(
        joinedload(WorkSpace.boxes).joinedload(Box.items),
        joinedload(WorkSpace.resources)
    ).filter(WorkSpace.id == workspace_id).first()

    if workspace_with_role is None:
        raise HTTPException(status_code=404, detail="WorkSpace not found")

    workspace, role = workspace_with_role
    
    # Create a dictionary from the workspace object and add the role
    workspace_dict = workspace.__dict__
    workspace_dict['role'] = role
    workspace_dict['boxes'] = [
        {**box.__dict__, 'items': [item.__dict__ for item in box.items]}
        for box in workspace.boxes
    ]
    workspace_dict['resources'] = [resource.__dict__ for resource in workspace.resources]

    return workspace_dict

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

@router.put("/{workspace_id}")
async def update_workspace(
    workspace_id: int,
    workspace: WorkSpaceSchema,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    # First, check if the workspace exists and is associated with the user
    db_workspace = db.query(WorkSpace).join(UserWorkSpace).filter(
        WorkSpace.id == workspace_id,
        UserWorkSpace.user_id == user_id, 
        UserWorkSpace.role == "owner" or UserWorkSpace.role == "admin"
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

# @router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_workspace(
#     workspace_id: int, 
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_user_id)
# ):
#     db_workspace = db.query(WorkSpace).join(UserWorkSpace).filter(
#         WorkSpace.id == workspace_id,
#         UserWorkSpace.user_id == user_id
#     ).first()
#     if db_workspace is None:
#         raise HTTPException(status_code=404, detail="WorkSpace not found")
#     db.delete(db_workspace)
#     db.commit()
#     return {"ok": True}

# Delete workspace for a single user
# @router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def leave_workspace(
#     workspace_id: int,
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_user_id)
# ):
#     user_workspace = db.query(UserWorkSpace).filter(
#         UserWorkSpace.work_space_id == workspace_id,
#         UserWorkSpace.user_id == user_id
#     ).first()
#     if user_workspace is None:
#         raise HTTPException(status_code=404, detail="WorkSpace not found or not associated with the user")
#     db.delete(user_workspace)
#     db.commit()
#     return {"ok": True}

# Allow deletion only for owners
@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    # Fetch the workspace and join with UserWorkSpace to check ownership
    workspace_with_user = db.query(WorkSpace).join(UserWorkSpace).filter(
        WorkSpace.id == workspace_id,
        UserWorkSpace.user_id == user_id,
        UserWorkSpace.role == "owner"
    ).first()

    if workspace_with_user is None:
        raise HTTPException(status_code=404, detail="Workspace not found or you're not authorized to delete it")
    
    # If we've reached this point, the workspace exists and the user is the owner
    db.delete(workspace_with_user)
    db.commit()
    return {"ok": True}
