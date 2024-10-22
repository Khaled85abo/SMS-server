from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.schemas.schemas import ResourceCreateSchema, ResourceSchema, ResourceUpdateSchema
from app.database.models.models import Resource, WorkSpace, User
from app.db_setup import get_db
from app.auth import get_user_id, get_user
from typing import List
import os
import shutil
from datetime import datetime

router = APIRouter()

UPLOAD_DIRECTORY = "resources/uploads"

from fastapi import Form

@router.post("/", response_model=ResourceSchema)
async def create_resource(
    resource: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    # Parse the JSON string into a ResourceCreateSchema object
    resource_data = ResourceCreateSchema.model_validate_json(resource)
    # Get the workspace
    workspace = db.query(WorkSpace).filter(WorkSpace.id == resource_data.work_space_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Create directory if it doesn't exist
    workspace_dir = os.path.join(UPLOAD_DIRECTORY, str(workspace.id))
    os.makedirs(workspace_dir, exist_ok=True)

    # Save the file
    file_path = os.path.join(workspace_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create resource in database
    db_resource = Resource(
        name=resource_data.name,
        description=resource_data.description,
        tags=resource_data.tags,
        status="added",
        work_space_id=resource_data.work_space_id,
        user_id=user_id,
        resource_type=file.content_type,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        file_extension=os.path.splitext(file.filename)[1],
    )

    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)

    return db_resource

@router.get("/", response_model=List[ResourceSchema])
async def get_resources(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    resources = db.query(Resource).filter(Resource.user_id == user_id).all()
    return resources

@router.get("/workspace/{workspace_id}", response_model=List[ResourceSchema])
async def get_resources(
    workspace_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    resources = db.query(Resource).filter(Resource.work_space_id == workspace_id).all()
    return resources

@router.get("/{resource_id}", response_model=ResourceSchema)
async def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

@router.put("/{resource_id}", response_model=ResourceSchema)
async def update_resource(
    resource_id: int,
    resource_update: ResourceUpdateSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
):
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    update_data = resource_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_resource, key, value)

    db_resource.updated_date = datetime.utcnow()
    db.commit()
    db.refresh(db_resource)

    return db_resource

@router.delete("/{resource_id}", status_code=204)
async def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
):
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Delete the file
    if os.path.exists(db_resource.file_path):
        os.remove(db_resource.file_path)

    db.delete(db_resource)
    db.commit()

    return {"detail": "Resource deleted"}

