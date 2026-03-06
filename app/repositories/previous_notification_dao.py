from app.core.supabase_client import supabase

class PreviousNotificationDAO:
    @staticmethod
    def save(notification: dict):
        """
        Save full notification data to 'previous_notifications' table.
        Expected keys: message, title, type, larvae_count,
                       density_per_cm2, temperature, humidity, timestamp
        """
        try:
            data = {
                "message":        notification.get("message"),
                "title":          notification.get("title"),
                "type":           notification.get("type"),
                "larvae_count":   notification.get("larvae_count"),
                "density_per_cm2": notification.get("density_per_cm2"),
                "temperature":    notification.get("temperature"),
                "humidity":       notification.get("humidity"),
                "timestamp":      notification.get("timestamp"),
            }
            # Remove None values so DB uses defaults
            data = {k: v for k, v in data.items() if v is not None}

            response = supabase.table("previous_notifications").insert(data).execute()
            print(f"✅ Notification saved to DB: {data}")
            return response
        except Exception as e:
            print(f"❌ Failed to save notification: {e}")
            raise

    @staticmethod
    def get_all():
        try:
            response = supabase.table("previous_notifications").select("*").execute()
            return response.data
        except Exception as e:
            print(f"❌ Failed to retrieve notifications: {e}")
            raise

    @staticmethod
    def delete_all():
        try:
            response = supabase.table("previous_notifications").delete().neq("id", 0).execute()
            print(f"✅ All previous notifications deleted from DB")
            return response
        except Exception as e:
            print(f"❌ Failed to delete all notifications: {e}")
            raise