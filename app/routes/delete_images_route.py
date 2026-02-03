from fastapi import APIRouter, HTTPException
from app.services.delete_images_service import DeleteImagesService

router = APIRouter(prefix="/api/images", tags=["Images"])

@router.delete("/delete-all")
async def delete_all_images():
    """
    Delete all saved images from storage and database.
    """
    try:
        result = DeleteImagesService.delete_all_saved_images()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_image(image_url: str):
    """
    Delete a specific image by URL.
    """
    try:
        result = DeleteImagesService.delete_image_by_url(image_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))