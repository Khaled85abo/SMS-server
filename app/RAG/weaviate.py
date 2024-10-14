from langchain_ollama import OllamaEmbeddings
import os
from langchain.embeddings.openai import OpenAIEmbeddings
import weaviate
from weaviate.classes.init import Auth
import weaviate.classes.config as wc
from weaviate.classes.query import Filter

embeddings_openai = OpenAIEmbeddings(openai_api_key = os.getenv("OPENAI_API_KEY"))
embeddings_llama = OllamaEmbeddings(
    model="mxbai-embed-large",
)

# Best practice: store your credentials in environment variables
wcd_url = os.environ["WEAVAITE_URL"]
wcd_api_key = os.environ["WEAVAITE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=wcd_url,  # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(wcd_api_key),  # Replace with your Weaviate Cloud key
    headers={'X-OpenAI-Api-key': openai_api_key}  # Replace with your OpenAI API key
)

# http://localhost:11434/api/embeddings
# ollama.embeddings(
#   model='mxbai-embed-large',
#   prompt='Llamas are members of the camelid family',
# )


def get_items_collection():
    return client.collections.get("Item")

def get_manuals_collection():
    return client.collections.get("Manual")

def create_weaviate_manuals():
    try:
        manuals = client.collections.get("Manual")
        print(manuals.config.get(simple=False))
    except Exception as e:
        manuals = client.collections.create(
            name="Manual",
            properties=[
                wc.Property(name="manual_id", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="content", data_type=wc.DataType.TEXT),
                wc.Property(name="type", data_type=wc.DataType.TEXT),
                wc.Property(name="workspace", data_type=wc.DataType.TEXT, skip_vectorization=True),
            ],
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(),
            generative_config=wc.Configure.Generative.openai(),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )
        print(manuals.config.get(simple=False))

def create_weaviate_schema():
    # Check if 'Item' class exists
    try:
        items =client.collections.get("Item")
        print(items.config.get(simple=False))
    except Exception as e:
        print("Item collection already exists: Creating new Item collection")
        client.collections.create(
            name="Item",
            properties=[
                wc.Property(name="item_id", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="name", data_type=wc.DataType.TEXT),
                wc.Property(name="description", data_type=wc.DataType.TEXT, optional=True),
                wc.Property(name="box", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="workspace", data_type=wc.DataType.TEXT, skip_vectorization=True),
            ],
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(),
            generative_config=wc.Configure.Generative.openai(),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )



def find_object_uuid(collection, db_id):
    results = collection.query.fetch_objects(
        filters=Filter.by_property("item_id").equal(db_id)
    )
    if results:
        print(results)
        result = results.objects
        # If we found a matching object, update it
        uuid = result[0].uuid
        print(f"UUID for {db_id}: {uuid}")
    else:
        print(f"No data found for item_id: {db_id}")


# Adding an item
def create_item(collection, properties):
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


def delete_item_from_weaviate(collection, item_id):
    collection.data.delete_by_id(uuid=item_id)


def search_item_by_keyword(collection, keyword):
    response = collection.query.bm25(
        query=keyword,
        limit=10,
    )

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


def create_weaviate_client( wcd_url, wcd_api_key, openai_api_key):
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=wcd_url,  # Replace with your Weaviate Cloud URL
        auth_credentials=Auth.api_key(wcd_api_key),  # Replace with your Weaviate Cloud key
        headers={'X-OpenAI-Api-key': openai_api_key}  # Replace with your OpenAI API key
    )
    return client