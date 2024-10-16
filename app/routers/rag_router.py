from fastapi import APIRouter, HTTPException, Depends
from app.RAG.weaviate import get_items_collection
from app.routers.item_router import get_items
from app.RAG.weaviate import serialize_items
from app.db_setup import get_db
from sqlalchemy.orm import Session
from weaviate.classes.query import Filter
from app.database.schemas.schemas import SearchDataSchema
router = APIRouter()



@router.post("/populate-db")
async def embed_db(db: Session = Depends(get_db)):
    try:
        items_db =await get_items(db=db)
        items_collection = get_items_collection()
        print("\033[1;35m" + "Items to be added:" + "\033[0m", items_db) 
        with items_collection.batch.dynamic() as batch:
            for item in items_db:
                print("\033[1;35m" + "Item to be added:" + "\033[0m", item)  # Bold magenta text
                batch.add_object(
                properties={
                    "item_id": item['id'],
                    "name": item['name'],
                    "description": item['description'],
                    "box": item['box'],
                    "workspace": item['workspace'],
                        })
            if batch.number_errors > 0:
                print("\033[1;31m" + "Error inserting items to weaviate" + "\033[0m")
        return {"message": "Db has been embedded!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error embedding db: {e}")


@router.post("/search")
async def keyword_search(search_data:SearchDataSchema  , db: Session = Depends(get_db)):
    print(search_data)
    try:
        query = search_data.query
        workspace = search_data.workspace
        type = search_data.type
        items_collection = get_items_collection()
        results=None
        if workspace:
            if type == "keyword":
                results = items_collection.query.bm25(
                    query=query,
                limit=10,
                    filters=Filter.by_property("workspace").equal(workspace)
                )
            else:
                results = items_collection.query.near_text(
                    query=query,
                    limit=10,
                    filters=Filter.by_property("workspace").equal(workspace)
                )
        else:
            if type == "keyword":
                results = items_collection.query.bm25(
                    query=query,
                    limit=10,
                )
            else:
                results = items_collection.query.near_text(
                    query=query,
                    limit=10,
                )
        return {"results": serialize_items(results)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error keyword searching: {e}")
    

