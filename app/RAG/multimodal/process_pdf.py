from unstructured.partition.pdf import partition_pdf
import os


# Get elements
raw_pdf_elements = partition_pdf(
    filename=os.path.join(input_path, "test.pdf"),
    extract_images_in_pdf=True,
    infer_table_structure=True,
    chunking_strategy="by_title",
    max_characters=4000,
    new_after_n_chars=3800,
    combine_text_under_n_chars=2000,
    image_output_dir_path=output_path,
)




def embed_pdf_to_weaviate(pdf_file_path, weaviate_collection_name):
    """
    Embeds the content of a PDF file into a Weaviate collection using LangChain and OpenAI embeddings.

    Parameters:
    - pdf_file_path (str): The path to the PDF file to be embedded.
    - weaviate_collection_name (str): The name of the Weaviate collection (class) where embeddings will be stored.

    Requirements:
    - The environment must have the following environment variables set:
        - OPENAI_API_KEY: Your OpenAI API key.
        - WEAVIATE_URL: The URL of your Weaviate instance.
        - WEAVIATE_API_KEY: Your Weaviate API key (if authentication is enabled).
    """

    import os
    import weaviate
    from langchain.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Weaviate

    # Load PDF and extract text
    loader = PyPDFLoader(pdf_file_path)
    documents = loader.load()

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings()

    # Initialize Weaviate client
    WEAVIATE_URL = os.environ.get("WEAVIATE_URL")
    WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    if not WEAVIATE_URL or not OPENAI_API_KEY:
        raise ValueError("Environment variables WEAVIATE_URL and OPENAI_API_KEY must be set.")

    if WEAVIATE_API_KEY:
        auth_config = weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY)
    else:
        auth_config = None

    client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=auth_config,
        additional_headers={
            "X-OpenAI-Api-Key": OPENAI_API_KEY
        }
    )

    # Check if the Weaviate class exists; if not, create it
    schema = client.schema.get()
    class_names = [c['class'] for c in schema['classes']]
    if weaviate_collection_name not in class_names:
        class_obj = {
            "class": weaviate_collection_name,
            "vectorizer": "none",  # We are using external embeddings
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                },
            ]
        }
        client.schema.create_class(class_obj)

    # Initialize the Weaviate vector store with embeddings
    vectorstore = Weaviate(
        client=client,
        index_name=weaviate_collection_name,
        text_key="text",
        embedding=embeddings
    )

    # Add documents to the vector store
    vectorstore.add_documents(docs)

    print(f"Successfully embedded {len(docs)} document chunks into Weaviate collection '{weaviate_collection_name}'.")


def embed_pdf_to_manual_collection(pdf_file_path, manual_id, type_, workspace, tags , manual_collection):
    """
    Embeds the content of a PDF file into the 'Manual' Weaviate collection using Unstructured's partition_pdf,
    LangChain's RecursiveCharacterTextSplitter, and stores them in Weaviate.

    Parameters:
    - pdf_file_path (str): The path to the PDF file to be embedded.
    - manual_id (str): The ID of the manual.
    - type_ (str): The type of the manual.
    - workspace (str): The workspace associated with the manual.
    - tags (str): Tags associated with the manual.

    Requirements:
    - The environment must have the following environment variables set:
        - WEAVIATE_URL: The URL of your Weaviate instance.
        - WEAVIATE_API_KEY: Your Weaviate API key (if authentication is enabled).
    """
    import os
    import weaviate
    from unstructured.partition.pdf import partition_pdf
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Step 1: Extract elements from PDF using Unstructured
    elements = partition_pdf(filename=pdf_file_path)

    # Extract text from elements and join them into a single string
    text_content = "\n\n".join(
        element.text for element in elements if hasattr(element, 'text') and element.text
    )

    # Check if any text was extracted
    if not text_content.strip():
        raise ValueError("No text could be extracted from the PDF.")

    # Step 2: Split text into chunks using RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(text_content)

    # Step 3: Initialize Weaviate client
    WEAVIATE_URL = os.environ.get("WEAVIATE_URL")
    WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")

    if not WEAVIATE_URL:
        raise ValueError("Environment variable WEAVIATE_URL must be set.")

    if WEAVIATE_API_KEY:
        auth_config = weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY)
    else:
        auth_config = None



    # Step 5: Prepare and add data to Weaviate
    # Extract file size and extension from the file path
    file_size = os.path.getsize(pdf_file_path)
    file_extension = os.path.splitext(pdf_file_path)[1]

    # Create batch and add data
    with manual_collection.batch as batch:
        batch.batch_size = 100
        for idx, chunk in enumerate(chunks):
            properties = {
                "manual_id": manual_id,
                "content": chunk,
                "type": type_,
                "workspace": workspace,
                "tags": tags,
                "file_path": pdf_file_path,
                "file_size": file_size,
                "file_extension": file_extension
            }
            batch.add_data_object(
                data_object=properties,
                # class_name=class_name
            )

    print(f"Successfully added {len(chunks)} document chunks into Weaviate collection '{class_name}'.")


import os

# Set environment variables before running
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["WEAVIATE_URL"] = "http://localhost:8080"
# If authentication is enabled in Weaviate
# os.environ["WEAVIATE_API_KEY"] = "your-weaviate-api-key"

# Define the properties for your manual
pdf_file_path = "example.pdf"
manual_id = "manual-123"
type_ = "User Guide"
workspace = "Engineering"
tags = "equipment, safety"
# Call the function
embed_pdf_to_manual_collection(
    pdf_file_path=pdf_file_path,
    manual_id=manual_id,
    type_=type_,
    workspace=workspace,
    tags=tags
)
