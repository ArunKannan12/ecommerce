from django.core.management.base import BaseCommand
from products.models import Category, ProductImage, ProductVariantImage
import cloudinary.uploader

class Command(BaseCommand):
    help = "Migrate local images to Cloudinary with organized folders"

    def handle(self, *args, **kwargs):
        model_folder_map = {
            Category: "ecommerce/categories/",
            ProductImage: "ecommerce/products/",
            ProductVariantImage: "ecommerce/variants/",
        }

        for model, folder in model_folder_map.items():
            for obj in model.objects.all():
                if obj.image and not obj.image_url:  # migrate only if not already migrated
                    self.stdout.write(self.style.WARNING(f"Uploading {obj.image.path} to {folder}..."))

                    try:
                        upload_result = cloudinary.uploader.upload(
                            obj.image.path,
                            folder=folder
                        )
                        obj.image_url = upload_result["secure_url"]
                        obj.image.delete(save=False)  # remove local file ref
                        obj.save()
                        self.stdout.write(self.style.SUCCESS(f"Uploaded -> {obj.image_url}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed: {e}"))
