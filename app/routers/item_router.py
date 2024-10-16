from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from app.db_setup import get_db
from app.database.models.models import Item, ItemImage, Box
from app.database.schemas.schemas import ItemPOSTSchema,ItemPUTSchema, ItemOutSchema
from app.routers.image_router import upload_image
from app.auth import get_user_id
import base64
from io import BytesIO
from uuid import uuid4
from typing import Annotated
from fastapi.responses import JSONResponse
from app.RAG.weaviate import client, get_items_collection, add_data, update_data, delete_data, find_item_uuid
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

# @router.post("/", response_model=ItemOutSchema)
# async def create_item(
#     name: str = Form(...),
#     description: str = Form(...),
#     quantity: int = Form(...),
#     box_id: int = Form(...),
#     image: Optional[UploadFile] = File(None),
#     image_base64: Optional[str] = Form(None),
#     db: Session = Depends(get_db)
# ):
#     # Create the item
#     item_data = {
#         "name": name,
#         "description": description,
#         "quantity": quantity,
#         "box_id": box_id
#     }
#     db_item = Item(**item_data)
#     db.add(db_item)
#     db.flush()  # Flush to get the item_id

#     # Handle image upload if present
#     if image or image_base64:
#         try:
#             if image:
#                 # Use the uploaded file directly
#                 file = image
#             elif image_base64:
#                 # Decode base64 image
#                 image_data = base64.b64decode(image_base64)
#                 file_extension = "png"  # You might want to determine this dynamically
#                 unique_filename = f"{uuid4()}.{file_extension}"
#                 file = UploadFile(filename=unique_filename, file=BytesIO(image_data))
            
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

@router.post("/", response_model=ItemOutSchema)
async def create_item(
    item: ItemPOSTSchema, 
    user_id: Annotated[int, Depends(get_user_id)],
    db: Session = Depends(get_db)
):
    try:
        # Start database transaction
        db.begin_nested()

        # Create the item in the database
        print(item)
        box = item.box
        workspace = item.workspace
        db_item = Item(**item.model_dump(exclude={'image', 'box', 'workspace'}))
        db.add(db_item)
        db.flush()  # Flush to get the item_id

        # Handle image upload if present
        if item.image:
            try:
                # Decode base64 image
                image_data = base64.b64decode(item.image)
                
                # Generate a unique filename
                file_extension = "png"  # You might want to determine this dynamically
                unique_filename = f"{uuid4()}.{file_extension}"
                
                # Create an UploadFile object with the unique filename
                file = UploadFile(filename=unique_filename, file=BytesIO(image_data))
                
                # Use the upload_image function with user_id
                image_result = await upload_image(file, user_id)
                print(image_result)
                image_url = image_result["imageURL"]
                print(image_url)
                
                # Create ItemImage record
                db_image = ItemImage(url=image_url, item_id=db_item.id)
                db.add(db_image)
            
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                    detail=f"Error processing image: {str(e)}")

        # Add the item to Weaviate
        try:
            items_collection = get_items_collection()
            add_data(collection=items_collection, properties={
                "item_id": db_item.id,
                "name": db_item.name,
                "description": db_item.description,
                "box": box,
                "workspace": workspace
            })
        except Exception as weaviate_error:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail=f"Weaviate operation failed: {str(weaviate_error)}")

        # If we've made it this far, commit the database transaction
        db.commit()
        db.refresh(db_item)

        return db_item

    except SQLAlchemyError as db_error:
        db.rollback()
        print(f"Database error occurred: {str(db_error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database operation failed: {str(db_error)}")

    except HTTPException:
        # Re-raise HTTP exceptions (like the ones we defined for Weaviate errors)
        raise

    except Exception as e:
        db.rollback()
        print(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"An unexpected error occurred: {str(e)}")

# @router.get("/")
# async def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = db.query(Item).options(joinedload(Item.images)).offset(skip).limit(limit).all()
    
#     # Convert items to dictionaries and include image objects
#     items_with_images = []
#     for item in items:
#         item_dict = item.__dict__
#         item_dict['images'] = [{"id": image.id, "url": image.url} for image in item.images]
#         item_dict['box'] = item.box.name if item.box else None
#         item_dict['workspace'] = item.box.work_space.name if item.box and item.box.work_space else None
#         item_dict.pop('_sa_instance_state', None)
#         items_with_images.append(item_dict)
    
#     return items_with_images

@router.get("/")
async def get_items( db: Session = Depends(get_db)):
    items = db.query(Item).options(joinedload(Item.images), joinedload(Item.box).joinedload(Box.work_space)).all()
    
    items_with_images_and_workspace = []
    for item in items:
        item_dict = {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'description': item.description,
            'status': item.status,
            'images': [{'id': image.id, 'url': image.url} for image in item.images],
            'box': item.box.name if item.box else None,
            'workspace': item.box.work_space.name if item.box and item.box.work_space else None
        }
        items_with_images_and_workspace.append(item_dict)

    return items_with_images_and_workspace

@router.get("/{item_id}")
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).options(joinedload(Item.images)).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Convert item to dictionary
    item_dict = item.__dict__
    
    # Format images as an array of objects with id and url
    item_dict['images'] = [{"id": image.id, "url": image.url} for image in item.images]
    
    # Remove the _sa_instance_state key
    # item_dict.pop('_sa_instance_state', None)
    
    return item_dict

@router.put("/{item_id}", response_model=ItemOutSchema)
async def update_item(item_id: int, item: ItemPUTSchema, db: Session = Depends(get_db)):
    try:
        db.begin_nested()

        db_item = db.query(Item).filter(Item.id == item_id).first()
        if db_item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Update the item in the database
        for key, value in item.model_dump(exclude={'image'}).items():
            if value is not None:
                setattr(db_item, key, value)

        # Update the item in Weaviate
        try:
            items_collection = get_items_collection()
            uuid = find_item_uuid(items_collection, item_id)
            if uuid:
                update_data(items_collection, uuid, {
                    "name": db_item.name,
                    "description": db_item.description,
                })
        except Exception as weaviate_error:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail=f"Weaviate operation failed: {str(weaviate_error)}")

        db.commit()
        db.refresh(db_item)

        return db_item

    except SQLAlchemyError as db_error:
        db.rollback()
        print(f"Database error occurred: {str(db_error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database operation failed: {str(db_error)}")

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        print(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"An unexpected error occurred: {str(e)}")

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Delete the item from the database
    db.delete(db_item)
    db.commit()

    # Delete the item from Weaviate
    items_collection = get_items_collection()
    uuid = find_item_uuid(items_collection, item_id)
    if uuid:
        delete_data(items_collection, uuid)

    return {"ok": True}
