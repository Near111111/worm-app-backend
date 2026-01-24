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