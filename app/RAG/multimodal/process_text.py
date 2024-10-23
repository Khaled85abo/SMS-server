from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.database.schemas.schemas import ResourceProcessingSchema
from app.RAG.weaviate import client
from app.database.models.models import Resource
from sqlalchemy.orm import Session
import os

# text_path = os.path.join(input_path, "state_of_the_union.txt")

# # Read the file content
# with open(text_path, 'r', encoding='utf-8') as file:
#     text_content = file.read()

# # Create a Document object
# document = Document(page_content=text_content)

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
# docs = text_splitter.split_documents([document])
# print(docs)
# for doc in docs:
#   print(doc.page_content)


def process_text(resource: ResourceProcessingSchema, db: Session):
    # Read the file content
    with open(resource.file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()

    # Create a Document object
    document = Document(page_content=text_content)

    # Split the document
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
    docs = text_splitter.split_documents([document])

    # Get the Resources collection
    resources_collection = client.collections.get("Resource")

    # Prepare batch object
    with resources_collection.batch.dynamic() as batch:
        for i, doc in enumerate(docs):
            properties = {
                "resource_id": str(resource.id),
                "content": doc.page_content,
                "workspace": resource.workspace,
                "tags": resource.tags,
                "file_path": resource.file_path,
                "file_size": resource.file_size,
                "file_extension": resource.file_extension,
                "file_name": os.path.basename(resource.file_path),
                "start_offset": i * 1000,  # Approximate offset
                "end_offset": (i + 1) * 1000,  # Approximate offset
                "resource_type": resource.resource_type,
                "paragraph_number": i + 1,
            }
            batch.add_object(properties=properties)

    # Update resource status in the database
    db_resource = db.query(Resource).filter(Resource.id == resource.id).first()
    if db_resource:
        db_resource.status = "processed"
        db.commit()

    return len(docs)  # Return the number of chunks processed
