from langchain_ollama import OllamaEmbeddings
import os
from langchain.embeddings.openai import OpenAIEmbeddings
import weaviate
from weaviate.classes.init import Auth
import weaviate.classes.config as wc

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
            vectorizer_config=wc.Configure.Vectorizer.text2vec_cohere(),
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
            vectorizer_config=wc.Configure.Vectorizer.text2vec_cohere(),
            generative_config=wc.Configure.Generative.openai(),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE,
            ),
        )