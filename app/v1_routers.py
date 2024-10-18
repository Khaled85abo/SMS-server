from fastapi import APIRouter
from .routers import user_router, login_router, image_router, detection_router, item_router, box_router, workspace_router, rag_router, resource_router

v1_router = APIRouter()


v1_router.include_router(user_router.router, prefix="/users", tags=["users"])
v1_router.include_router(login_router.router, prefix="/login", tags=["login"])
v1_router.include_router(detection_router.router, prefix="/detection", tags=["detection"])
v1_router.include_router(image_router.router, prefix="/images", tags=["images"])
v1_router.include_router(item_router.router, prefix="/items", tags=["items"])
v1_router.include_router(box_router.router, prefix="/boxes", tags=["boxes"])
v1_router.include_router(workspace_router.router, prefix="/workspaces", tags=["workspaces"])
v1_router.include_router(rag_router.router, prefix="/rag", tags=["rag"])
v1_router.include_router(resource_router.router, prefix="/resources", tags=["resources"])


