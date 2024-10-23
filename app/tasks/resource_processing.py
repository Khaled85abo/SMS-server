import logging
from celery import shared_task
from sqlalchemy.orm import Session
from app.db_setup import engine
from app.database.models.models import Resource
from app.database.schemas.schemas import ResourceProcessingSchema
from typing import Dict, Any
# from app.RAG.multimodal.process_text import process_text
# from app.RAG.multimodal.process_pdf import process_pdf
# from app.RAG.multimodal.process_image import process_image
# from app.RAG.multimodal.process_video import process_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task
def process_resource_task(resource_data: ResourceProcessingSchema):
    logger.info(f"Starting to process resource {resource_data['id']}")
    try:
        # Update status to processing
        logger.info(f"Updating status of resource {resource_data['id']} to processing")
        update_resource_status(resource_data['id'], "processing")

        # Process the resource based on its file type
        logger.info(f"Processing resource {resource_data['id']} of type {resource_data['file_type']}")
        if resource_data['file_type'] == 'pdf':
            process_pdf(resource_data)
        elif resource_data['file_type'] == 'image':
            process_image(resource_data)
        elif resource_data['file_type'] == 'video':
            process_video(resource_data)
        elif resource_data['file_type'] == 'text':
            process_text(resource_data)
        else:
            raise ValueError(f"Unsupported file type: {resource_data['file_type']}")

        # Update status to completed
        logger.info(f"Updating status of resource {resource_data['id']} to completed")
        update_resource_status(resource_data['id'], "completed")
        logger.info(f"Successfully processed resource {resource_data['id']}")
    except Exception as e:
        logger.error(f"Error processing resource {resource_data['id']}: {str(e)}")
        # Update status to failed
        update_resource_status(resource_data['id'], "failed")

def update_resource_status(resource_id: int, status: str):
    with Session(engine) as db:
        db.query(Resource).filter(Resource.id == resource_id).update({"status": status})
        db.commit()

# Note: The following functions are placeholders. You'll need to implement the actual processing logic.

def process_pdf(resource_data: Dict[str, Any]):
    logger.info(f"Processing PDF: {resource_data['name']}")
    # Implement PDF processing logic here
    # Use resource_data to create Weaviate embeddings

def process_image(resource_data: Dict[str, Any]):
    logger.info(f"Processing Image: {resource_data['name']}")
    # Implement image processing logic here
    # Use resource_data to create Weaviate embeddings

def process_video(resource_data: Dict[str, Any]):
    logger.info(f"Processing Video: {resource_data['name']}")
    # Implement video processing logic here
    # Use resource_data to create Weaviate embeddings

def process_text(resource_data: Dict[str, Any]):
    logger.info(f"Processing Text: {resource_data['name']}")
    # Implement text processing logic here
    # Use resource_data to create Weaviate embeddings
