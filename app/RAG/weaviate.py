# from langchain_ollama import OllamaEmbeddings
import os
# from langchain.embeddings.openai import OpenAIEmbeddings
import weaviate
from weaviate.classes.init import Auth
import weaviate.classes.config as wc
from weaviate.classes.query import Filter
# from app.routers.item_router import get_items
# embeddings_openai = OpenAIEmbeddings(openai_api_key = os.getenv("OPENAI_API_KEY"))
# embeddings_llama = OllamaEmbeddings(
#     model="mxbai-embed-large",
# )

# Best practice: store your credentials in environment variables
wcd_url = os.environ["WEAVAITE_URL"]
wcd_api_key = os.environ["WEAVAITE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=wcd_url,  # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(wcd_api_key),  # Replace with your Weaviate Cloud key
    headers={'X-OpenAI-Api-key': openai_api_key}  # Replace with your OpenAI API key
)

# def create_weaviate_client():   
#     client = weaviate.connect_to_weaviate_cloud(
#         cluster_url=wcd_url,  # Replace with your Weaviate Cloud URL
#         auth_credentials=Auth.api_key(wcd_api_key),  # Replace with your Weaviate Cloud key
#         headers={'X-OpenAI-Api-key': openai_api_key}  # Replace with your OpenAI API key
#     )
#     return client


async def init_weaviate():
    # await create_weaviate_resouce_collection()
    await create_weaviate_item_collection()



# async def insert_items_to_weaviate(items_collection):
#     print("inserting items to weaviate")
#     print(items_collection)
#     items_db =await get_items()
#     print(items_db)
#     with items_collection.batch.dynamic() as batch:
#         for item in items_db:
#             batch.add_object(
#             properties={
#                 "item_id": item.id,
#                 "name": item.name,
#                 "description": item.description,
#                 "box": item.box,
#                 "workspace": item.workspace,
#                 })
#             if batch.number_errors > 100:
#                 print("Error inserting items to weaviate")



def get_items_collection():
    return client.collections.get("Item")

def get_resouces_collection():
    return client.collections.get("Resource")

async def create_weaviate_resource_collection():
    try:
        sources = client.collections.get("Resource")
        print(sources.config.get(simple=False))
    except Exception as e:
        sources = client.collections.create(
            name="Resource",
            properties=[
                wc.Property(name="resource_id", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="content", data_type=wc.DataType.TEXT),
                wc.Property(name="workspace", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="tags", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="file_path", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="file_size", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="file_extension", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="file_name", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="start_offset", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="end_offset", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="page_number", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="resource_type", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="timestamp", data_type=wc.DataType.FLOAT, skip_vectorization=True),  # For audio/video
                wc.Property(name="paragraph_number", data_type=wc.DataType.INT, skip_vectorization=True),
            ],
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(model="text-embedding-3-large"),
            generative_config=wc.Configure.Generative.openai(
                model="gpt-4o",
                max_tokens=128000
            ),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )
        print(sources.config.get(simple=False))

async def create_weaviate_item_collection():
    # Check if 'Item' class exists
    try:
        items =client.collections.get("Item")
        print(items.config.get(simple=False))
    except Exception as e:
        print("Item collection does not exist: Creating new Item collection")
        items = client.collections.create(
            name="Item",
            properties=[
                wc.Property(name="item_id", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="name", data_type=wc.DataType.TEXT),
                wc.Property(name="description", data_type=wc.DataType.TEXT, optional=True),
                wc.Property(name="box", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="workspace", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="workspace_id", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="box_id", data_type=wc.DataType.INT, skip_vectorization=True),
            ],
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(model="text-embedding-3-large"),
            generative_config=wc.Configure.Generative.openai(
                model="gpt-4o",
                max_tokens=128000
            ),  
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )
        # await insert_items_to_weaviate(items_collection=items)

def find_resource_uuid(collection, db_id):
    results = collection.query.fetch_objects(
        filters=Filter.by_property("resource_id").equal(db_id)
    )
    if len(results.objects) > 0:
        print(results)
        result = results.objects
        # If we found a matching object, update it
        uuid = result[0].uuid
        print(f"UUID for {db_id}: {uuid}")
        return uuid
    else:
        print(f"No data found for resource_id: {db_id}")
        return None


def find_item_uuid(collection, db_id):
    results = collection.query.fetch_objects(
        filters=Filter.by_property("item_id").equal(db_id)
    )
    if len(results.objects) > 0:
        print(results)
        result = results.objects
        # If we found a matching object, update it
        uuid = result[0].uuid
        print(f"UUID for {db_id}: {uuid}")
        return uuid
    else:
        print(f"No data found for item_id: {db_id}")
        return None



# Adding an item
def add_data(collection, properties):
    collection.data.insert(
        properties= properties,
    )


def update_data(collection,uuid, properties):
# Update data
    collection.data.update(
        uuid=uuid,
        properties=properties,
        # operation="merge"  # Use "merge" to update only specified properties

    )

def delete_data(collection, uuid):
    collection.data.delete_by_id(uuid=uuid)

def delete_many_by_id(collection, property, value):
    collection.data.delete_many(
        where=Filter.by_property(property).equal(value)
    )


def keyword_items_search(collection, keyword, workspace):
    response = collection.query.bm25(
        query=keyword,
        limit=10,
        filters=Filter.by_property("workspace").equal(workspace)
    )
    return response

def semantic_items_search(collection, query, workspace, limit=5):
    response = collection.query.near_text(
        query=query,
        limit=limit,
        filters=Filter.by_property("workspace").equal(workspace)
    )
    return response


def serialize_items(response):
    results = []
    for obj in response.objects:
        # Accessing UUID
        item = {}
        item["uuid"] = obj.uuid
        item["name"] = obj.properties['name']
        item["description"] = obj.properties['description']
        item["box"] = obj.properties['box']
        item["item_id"] = obj.properties['item_id']
        item["workspace"] = obj.properties['workspace']
        item["workspace_id"] = obj.properties['workspace_id']
        item["box_id"] = obj.properties['box_id']
        results.append(item)
    return results

# def add_resouce_to_weaviate(client, resouce_id, content, type, workspace):
#     client.data_object.create(
#         data_object={
#             "resouce_id": resouce_id,
#             "content": content,
#             "type": type,
#             "workspace": workspace,
#         },
#         class_name="Resouce",
#     )


def search_items(workspace, query, type, limit=10):
    items_collection = get_items_collection()
    if workspace:
        if type == "keyword":
            results = items_collection.query.bm25(
                query=query,
            limit=limit,
                filters=Filter.by_property("workspace").equal(workspace)
            )
        else:
            results = items_collection.query.near_text(
                query=query,
                limit=limit,
                filters=Filter.by_property("workspace").equal(workspace)
            )
    else:
        if type == "keyword":
            results = items_collection.query.bm25(
                query=query,
                limit=limit,
            )
        else:
            results = items_collection.query.near_text(
                query=query,
                limit=limit,
            )
    return results


def semantic_search_items(workspace, query, type, limit=10):

    # prompt =f"return the items that are related to: {query}, no explanation needed! if no items match, return empty array"
    # prompt =f"return the items that are related to the: {query}, explain it to yourself, but do not return the explanation! if no items match, return nothing"
    prompt =f"return all the items that are related to '{query}', NO explanation needed! if no items match, return nothing at all"
    items_collection = get_items_collection()
    if workspace:
        if type == "keyword":
            results = items_collection.generate.bm25(
                query=query,
            limit=limit,
                filters=Filter.by_property("workspace").equal(workspace),
                grouped_task=prompt
            )
        else:
            results = items_collection.generate.near_text(
                query=query,
                limit=limit,
                filters=Filter.by_property("workspace").equal(workspace),
                grouped_task=prompt
            )
    else:
        if type == "keyword":
            results = items_collection.generate.bm25(
                query=query,
                limit=limit,
                grouped_task=prompt
            )
        else:
            results = items_collection.generate.near_text(
                query=query,
                limit=limit,
                grouped_task=prompt
            )
    return results 



def close_client():
    client.close() 
