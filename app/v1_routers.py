from fastapi import APIRouter
from .routers import image_router,  detection_router, app_router

v1_router = APIRouter()


v1_router.include_router(detection_router.router , prefix="/detection" , tags=["detection"])
v1_router.include_router(app_router.router , prefix="/app" , tags=["app"])
v1_router.include_router(image_router.router , prefix="/images" , tags=["images"])


