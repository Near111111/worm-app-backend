from app.repositories.saved_images_dao import SavedImagesDAO
from app.core.supabase_client import supabase

class DeleteImagesService:
    @staticmethod
    def delete_all_saved_images():
        """
        Delete all saved images from both database and Supabase Storage.
        Returns a summary of the deletion operation.
        """
        try:
            # Get all image URLs first before deleting from DB
            saved_images = SavedImagesDAO.get_all()
            
            if not saved_images:
                print("ℹ️ No images to delete")
                return {
                    "success": True,
                    "message": "No images found to delete",
                    "deleted_count": 0
                }
            
            deleted_from_storage = 0
            failed_storage_deletes = []
            
            # Delete from Supabase Storage
            bucket = supabase.storage.from_("snapshots")
            for image in saved_images:
                try:
                    # Extract filename from URL
                    url = image.get("image_metadata", "")
                    filename = url.split("/")[-1]
                    
                    bucket.remove([filename])
                    deleted_from_storage += 1
                    print(f"🗑️ Deleted from storage: {filename}")
                    
                except Exception as e:
                    failed_storage_deletes.append(filename)
                    print(f"⚠️ Failed to delete {filename} from storage: {e}")
            
            # Delete all from database
            SavedImagesDAO.delete_all()
            
            result = {
                "success": True,
                "message": "All saved images deleted successfully",
                "total_images": len(saved_images),
                "deleted_from_storage": deleted_from_storage,
                "failed_storage_deletes": failed_storage_deletes,
                "deleted_from_db": len(saved_images)
            }
            
            print(f"✅ Deletion complete: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Failed to delete all saved images: {e}")
            raise
    
    @staticmethod
    def delete_image_by_url(image_url: str):
        """
        Delete a specific image by its URL from both storage and database.
        """
        try:
            # Extract filename from URL
            filename = image_url.split("/")[-1]
            
            # Delete from storage
            bucket = supabase.storage.from_("snapshots")
            bucket.remove([filename])
            print(f"🗑️ Deleted from storage: {filename}")
            
            # Delete from database
            response = supabase.table("saved_images")\
                .delete()\
                .eq("image_metadata", image_url)\
                .execute()
            
            print(f"✅ Image deleted: {image_url}")
            return {
                "success": True,
                "message": "Image deleted successfully",
                "deleted_url": image_url
            }
            
        except Exception as e:
            print(f"❌ Failed to delete image: {e}")
            raise