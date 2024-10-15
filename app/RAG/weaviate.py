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
    # await create_weaviate_manual_collection()
    await create_weaviate_item_collection()


def insert_manuals_to_weaviate(manuals_collection):
    pass

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

def get_manuals_collection():
    return client.collections.get("Manual")

async def create_weaviate_manual_collection():
    try:
        manuals = client.collections.get("Manual")
        print(manuals.config.get(simple=False))
    except Exception as e:
        manuals = client.collections.create(
            name="Manual",
            properties=[
                wc.Property(name="manual_id", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="content", data_type=wc.DataType.TEXT),
                wc.Property(name="type", data_type=wc.DataType.TEXT , skip_vectorization=True),
                wc.Property(name="workspace", data_type=wc.DataType.TEXT, skip_vectorization=True),
            ],
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(model="text-embedding-3-large"),
            generative_config=wc.Configure.Generative.openai(),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )
        print(manuals.config.get(simple=False))
        await insert_manuals_to_weaviate(manuals_collection=manuals)

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
            ],
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(model="text-embedding-3-large"),
            generative_config=wc.Configure.Generative.openai(),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )
        # await insert_items_to_weaviate(items_collection=items)



def find_item_uuid(collection, db_id):
    results = collection.query.fetch_objects(
        filters=Filter.by_property("item_id").equal(db_id)
    )
    if results:
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


def get_item_details(response):
    for obj in response.objects:
        # Accessing UUID
        uuid = obj.uuid
        print("UUID:", uuid)

        # Accessing Metadata (if needed)
        creation_time = obj.metadata.creation_time
        print("Creation Time:", creation_time)

        # Accessing properties
        properties = obj.properties
        workspace = properties['workspace']
        description = properties['description']
        box = properties['box']
        item_id = properties['item_id']
        name = properties['name']

        print("Workspace:", workspace)
        print("Description:", description)
        print("Box:", box)
        print("Item ID:", item_id)
        print("Name:", name)

        # Accessing collection if needed
        collection = obj.collection
        print("Collection:", collection)
    return response

def add_manual_to_weaviate(client, manual_id, content, type, workspace):
    client.data_object.create(
        data_object={
            "manual_id": manual_id,
            "content": content,
            "type": type,
            "workspace": workspace,
        },
        class_name="Manual",
    )


def close_client(client):
    client.close() 