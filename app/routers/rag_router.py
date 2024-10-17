from fastapi import APIRouter, HTTPException, Depends
from app.RAG.weaviate import get_items_collection, search_items,semantic_search_items
from app.routers.item_router import get_items
from app.RAG.weaviate import serialize_items
from app.db_setup import get_db
from sqlalchemy.orm import Session
from weaviate.classes.query import Filter
from app.database.schemas.schemas import SearchDataSchema
router = APIRouter()



@router.post("/embed-db")
async def embed_db(db: Session = Depends(get_db)):
    try:
        items_db =await get_items(db=db)
        items_collection = get_items_collection()
        print("\033[1;35m" + "Items to added:" + "\033[0m", items_db) 
        with items_collection.batch.dynamic() as batch:
            for item in items_db:
                print("\033[1;35m" + "Add item:" + "\033[0m", item)  # Bold magenta text
                batch.add_object(
                properties={
                    "item_id": item['id'],
                    "name": item['name'],
                    "description": item['description'],
                    "box": item['box'],
                    "workspace": item['workspace'],
                    "workspace_id": item['workspace_id'],
                    "box_id": item['box_id'],
                        })
            if batch.number_errors > 0:
                print("\033[1;31m" + "Error inserting items to weaviate" + "\033[0m")
        return {"message": "Db has been embedded!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error embedding db: {e}")


@router.post("/search")
async def keyword_search(data:SearchDataSchema  , db: Session = Depends(get_db)):
    try:
        if data.use_ai_filter:
            results=semantic_search_items(workspace =data.workspace,query=data.query,type=data.type)
            return{"generated_result":results.generated, "results":serialize_items(results)}
        else:
            results=search_items(workspace =data.workspace,query=data.query,type=data.type)
            return {"results": serialize_items(results)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error keyword searching: {e}")
    

# @router.post("/semantic-search")
# async def semantic_search(data:SearchDataSchema  , db: Session = Depends(get_db)):
#     try:
#         results=semantic_search_items(workspace=data.workspace,query=data.query,type=data.type)
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=500, detail=f"Error semantic searching: {e}")
    

