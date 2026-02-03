from fastapi import APIRouter, HTTPException
from app.services.delete_notifications_service import DeleteNotificationsService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.delete("/delete-all")
async def delete_all_notifications():
    """
    Delete all previous notifications from the database.
    """
    try:
        result = DeleteNotificationsService.delete_all_notifications()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{notification_id}")
async def delete_notification(notification_id: int):
    """
    Delete a specific notification by ID.
    """
    try:
        result = DeleteNotificationsService.delete_notification_by_id(notification_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))