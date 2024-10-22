from fastapi import FastAPI, UploadFile, APIRouter,  HTTPException, Depends, status
from fastapi.responses import FileResponse
from app.dependencies.validate_token import verify_token
from uuid import uuid4
import os
from typing import Annotated
from app.auth import get_user_id
from app.db_setup import get_db
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, and_
from app.database.models import ItemImage



IMAGEDIR = "static/media/images/"

router = APIRouter()


@router.post("", status_code=201)
async def upload_image(file: UploadFile,  user_id: Annotated[int, Depends(get_user_id)]):

    accepted_img_extensions = ['jpg', 'jpeg', 'bmp', 'webp', 'png']
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No image provided")
    filename = file.filename
    filename_splitted = filename.split(".")
    file_extension = filename_splitted[-1]
    new_img_name = uuid4()
    if file_extension not in accepted_img_extensions:
        raise HTTPException(
            status_code=400, detail="Image extension is not supported")
    file.filename = f"{new_img_name}.{file_extension}"
    contents = await file.read()
    with open(f"{IMAGEDIR}{file.filename}", "wb") as f:
        f.write(contents)
    return {"imageURL": f"{IMAGEDIR}{file.filename}", "user_id": user_id}




@router.get("/display/{image_name}", status_code=200)
def get_image_with_name(image_name: str):
    # Add validation, image belongs to user
    images = os.listdir(IMAGEDIR)
    return FileResponse(f"{IMAGEDIR}{image_name}")


@router.delete("/{image_url}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_url: str, db: Session = Depends(get_db)):
    """
    Deletes an image based on an url
    """
    db_image = db.scalars(select(ItemImage).where(
        ItemImage.url == image_url)).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(db_image)
    db.commit()
    return {}