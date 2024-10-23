from celery import shared_task
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db_setup import get_db
from app.database.models.models import Resource
from app.RAG.multimodal.process_text import process_text
# from app.RAG.multimodal.process_pdf import process_pdf
# from app.RAG.multimodal.process_image import process_image
# from app.RAG.multimodal.process_video import process_video

@shared_task
def process_resource_task(resource_id: int, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).join(Resource.work_space).filter(Resource.id == resource_id).first()
        if not resource:
            print(f"Resource {resource_id} not found")
            return

        # Update status to processing
        resource.status = "processing"
        db.commit()

        # Process the resource based on its file type
        if resource.file_type == 'pdf':
            # process_pdf(resource)
            pass
        elif resource.file_type == 'image':
            # process_image(resource)
            pass
        elif resource.file_type == 'video':
            # process_video(resource)
            pass
        elif resource.file_type == 'text':
            # process_text(resource)
            pass
        else:
            raise ValueError(f"Unsupported file type: {resource.file_type}")

        # Update status to completed
        resource.status = "completed"
        db.commit()
    except Exception as e:
        print(f"Error processing resource {resource_id}: {str(e)}")
        # Update status to failed
        resource.status = "failed"
        db.commit()
    finally:
        db.close()
