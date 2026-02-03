from app.core.supabase_client import supabase

class PreviousNotificationDAO:
    @staticmethod
    def save(message: str):
        try:
            response = supabase.table("previous_notifications").insert({
                "message": message
            }).execute()
            print(f"✅ Notification saved to DB: {message}")
            return response
        except Exception as e:
            print(f"❌ Failed to save notification: {e}")
            raise
    
    @staticmethod
    def get_all():
        """
        Retrieve all previous notifications from the 'previous_notifications' table.
        """
        try:
            response = supabase.table("previous_notifications").select("*").execute()
            return response.data
        except Exception as e:
            print(f"❌ Failed to retrieve notifications: {e}")
            raise
    
    @staticmethod
    def delete_all():
        """
        Delete all records from the 'previous_notifications' table.
        """
        try:
            response = supabase.table("previous_notifications").delete().neq("id", 0).execute()
            print(f"✅ All previous notifications deleted from DB")
            return response
        except Exception as e:
            print(f"❌ Failed to delete all notifications: {e}")
            raise