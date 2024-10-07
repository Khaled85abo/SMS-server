from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db_setup import get_db
from app.database.models.models import Item, ItemImage
from app.database.schemas.schemas import ItemSchema, ItemOutSchema
from app.routers.image_router import upload_image
import base64
from io import BytesIO
from uuid import uuid4
from typing import Optional

router = APIRouter()

@router.post("/", response_model=ItemOutSchema)
async def create_item(
    name: str = Form(...),
    description: str = Form(...),
    quantity: int = Form(...),
    box_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Create the item
    item_data = {
        "name": name,
        "description": description,
        "quantity": quantity,
        "box_id": box_id
    }
    db_item = Item(**item_data)
    db.add(db_item)
    db.flush()  # Flush to get the item_id

    # Handle image upload if present
    if image or image_base64:
        try:
            if image:
                # Use the uploaded file directly
                file = image
            elif image_base64:
                # Decode base64 image
                image_data = base64.b64decode(image_base64)
                file_extension = "png"  # You might want to determine this dynamically
                unique_filename = f"{uuid4()}.{file_extension}"
                file = UploadFile(filename=unique_filename, file=BytesIO(image_data))
            
            # Use the upload_image function
            image_url = await upload_image(file)
            
            # Create ItemImage record
            db_image = ItemImage(url=image_url, item_id=db_item.id)
            db.add(db_image)
        
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Error processing image: {str(e)}")

    # Commit the transaction
    db.commit()
    db.refresh(db_item)
    return db_item

# @router.post("/", response_model=ItemOutSchema)
# async def create_item(item: ItemSchema, db: Session = Depends(get_db)):
#     # Create the item
#     db_item = Item(**item.dict(exclude={'image'}))
#     db.add(db_item)
#     db.flush()  # Flush to get the item_id

#     # Handle image upload if present
#     if item.image:
#         try:
#             # Decode base64 image
#             image_data = base64.b64decode(item.image)
            
#             # Generate a unique filename
#             file_extension = "png"  # You might want to determine this dynamically
#             unique_filename = f"{uuid4()}.{file_extension}"
            
#             # Create an UploadFile object with the unique filename
#             file = UploadFile(filename=unique_filename, file=BytesIO(image_data))
            
#             # Use the upload_image function
#             image_url = await upload_image(file)
            
#             # Create ItemImage record
#             db_image = ItemImage(url=image_url, item_id=db_item.id)
#             db.add(db_image)
        
#         except Exception as e:
#             db.rollback()
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
#                                 detail=f"Error processing image: {str(e)}")

#     # Commit the transaction
#     db.commit()
#     db.refresh(db_item)
#     return db_item

@router.get("/")
async def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@router.get("/{item_id}", response_model=ItemOutSchema)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemOutSchema)
async def update_item(item_id: int, item: ItemSchema, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"ok": True}