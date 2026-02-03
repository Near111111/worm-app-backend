from app.core.supabase_client import supabase

class SavedImagesDAO:
    @staticmethod
    def save(image_url: str):
        """
        Save the public URL of a snapshot to the 'saved_images' table.
        """
        try:
            data = {"image_metadata": image_url}
            response = supabase.table("saved_images").insert(data).execute()
            print(f"✅ Image saved to DB: {image_url}")
            return response
        except Exception as e:
            print(f"❌ Failed to save image: {e}")
            raise
    
    @staticmethod
    def get_all():
        """
        Retrieve all saved images from the 'saved_images' table.
        """
        try:
            response = supabase.table("saved_images").select("*").execute()
            return response.data
        except Exception as e:
            print(f"❌ Failed to retrieve images: {e}")
            raise
    
    @staticmethod
    def delete_all():
        """
        Delete all records from the 'saved_images' table.
        """
        try:
            response = supabase.table("saved_images").delete().neq("id", 0).execute()
            print(f"✅ All saved images deleted from DB")
            return response
        except Exception as e:
            print(f"❌ Failed to delete all images: {e}")
            raise