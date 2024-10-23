from celery import shared_task
from app.database.models.models import Resource
from app.db_setup import SessionLocal
from app.vectorization import process_pdf, process_image, process_video, process_text

@shared_task
def process_resource_task(resource_id: int):
    db = SessionLocal()
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            print(f"Resource {resource_id} not found")
            return

        # Update status to processing
        resource.status = "processing"
        db.commit()

        # Process the resource based on its file type
        if resource.file_type == 'pdf':
            process_pdf(resource)
        elif resource.file_type == 'image':
            process_image(resource)
        elif resource.file_type == 'video':
            process_video(resource)
        elif resource.file_type == 'text':
            process_text(resource)
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
