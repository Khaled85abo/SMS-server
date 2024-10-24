from langchain_unstructured import UnstructuredLoader
import os
from app.RAG.weaviate import get_resouces_collection
from app.database.schemas.schemas import ResourceProcessingSchema



UNSTRUCTURED_API_KEY=os.getenv("UNSTRUCTURED_API_KEY")




def process_pdf(resource:ResourceProcessingSchema):
    loader = UnstructuredLoader(
    file_path=resource.file_path,
    api_key=os.getenv("UNSTRUCTURED_API_KEY"),
        partition_via_api=True,
    )
    docs = loader.load()
    resources_collection = get_resouces_collection()

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
                "page_number": doc.metadata.get("page_number"),
                "resource_type": resource.resource_type,
                "paragraph_number": i + 1,
            }
            batch.add_object(properties=properties)

