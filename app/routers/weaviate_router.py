from fastapi import APIRouter, Request, HTTPException, Depends
from app.RAG.weaviate import get_items_collection
from app.routers.item_router import get_items
from app.db_setup import get_db
from sqlalchemy.orm import Session
router = APIRouter()


@router.post("/")
async def embed_db(db: Session = Depends(get_db)):
    try:
        items_db =await get_items(db=db)
        items_collection = get_items_collection()
        print(items_db)
        with items_collection.batch.dynamic() as batch:
            for item in items_db:
                batch.add_object(
                properties={
                    "item_id": item['id'],
                    "name": item['name'],
                    "description": item['description'],
                    "box": item['box'],
                    "workspace": item['workspace'],
                        })
                return {"message": "Db has been embedded!"}
            if batch.number_errors > 100:
                print("Error inserting items to weaviate")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error embedding db: {e}")
