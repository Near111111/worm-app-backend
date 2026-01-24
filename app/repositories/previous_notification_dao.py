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