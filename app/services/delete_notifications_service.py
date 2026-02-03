from app.repositories.previous_notification_dao import PreviousNotificationDAO
from app.core.supabase_client import supabase

class DeleteNotificationsService:
    @staticmethod
    def delete_all_notifications():
        """
        Delete all previous notifications from the database.
        Returns a summary of the deletion operation.
        """
        try:
            # Get all notifications first
            notifications = PreviousNotificationDAO.get_all()
            
            if not notifications:
                print("ℹ️ No notifications to delete")
                return {
                    "success": True,
                    "message": "No notifications found to delete",
                    "deleted_count": 0
                }
            
            # Delete all from database
            PreviousNotificationDAO.delete_all()
            
            result = {
                "success": True,
                "message": "All notifications deleted successfully",
                "deleted_count": len(notifications)
            }
            
            print(f"✅ Deletion complete: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Failed to delete all notifications: {e}")
            raise
    
    @staticmethod
    def delete_notification_by_id(notification_id: int):
        """
        Delete a specific notification by its ID.
        """
        try:
            response = supabase.table("previous_notifications")\
                .delete()\
                .eq("id", notification_id)\
                .execute()
            
            print(f"✅ Notification deleted: ID {notification_id}")
            return {
                "success": True,
                "message": "Notification deleted successfully",
                "deleted_id": notification_id
            }
            
        except Exception as e:
            print(f"❌ Failed to delete notification: {e}")
            raise