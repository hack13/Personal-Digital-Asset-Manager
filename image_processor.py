import os
from PIL import Image
from wand.image import Image as WandImage
import io
from typing import BinaryIO, Tuple, Optional

class ImageProcessor:
    @staticmethod
    def is_animated_gif(file_storage) -> bool:
        """Check if the image is an animated GIF"""
        try:
            # Save current position
            pos = file_storage.tell()
            # Go to beginning
            file_storage.seek(0)
            
            with Image.open(file_storage) as img:
                try:
                    img.seek(1)  # Try to move to the second frame
                    is_animated = True
                except EOFError:
                    is_animated = False
            
            # Restore position
            file_storage.seek(pos)
            return is_animated
        except Exception:
            # Restore position in case of error
            file_storage.seek(pos)
            return False

    @staticmethod
    def convert_to_webp(file_storage, quality: int = 90) -> Tuple[BinaryIO, str]:
        """
        Convert an image to WebP format.
        Returns a tuple of (file_object, extension)
        """
        # Save current position
        pos = file_storage.tell()
        # Go to beginning
        file_storage.seek(0)

        try:
            # Check if it's an animated GIF
            if ImageProcessor.is_animated_gif(file_storage):
                # Convert animated GIF to animated WebP
                file_storage.seek(0)
                with WandImage(file=file_storage) as img:
                    # Configure WebP animation settings
                    img.format = 'WEBP'
                    
                    # Higher quality settings for animation
                    img.options['webp:lossless'] = 'true'  # Use lossless for animations
                    img.options['webp:method'] = '6'       # Best compression method
                    img.options['webp:image-hint'] = 'graph'  # Better for animations
                    img.options['webp:minimize-size'] = 'false'  # Prioritize quality
                    
                    # Animation specific settings
                    img.options['webp:animation-type'] = 'default'
                    img.options['webp:loop'] = '0'  # Infinite loop
                    
                    # Save with high quality
                    webp_bytes = io.BytesIO(img.make_blob(format='webp'))
                    webp_bytes.seek(0)
                    return webp_bytes, '.webp'
            else:
                # Handle static images
                file_storage.seek(0)
                with Image.open(file_storage) as img:
                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.getchannel('A'))
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Save as WebP with high quality
                    output = io.BytesIO()
                    img.save(output, 
                           format='WEBP', 
                           quality=quality,      # Higher quality
                           method=6,             # Best compression method
                           lossless=False,       # Use lossy for static images
                           exact=True)           # Preserve color exactness
                    output.seek(0)
                    return output, '.webp'
        finally:
            # Restore original position
            file_storage.seek(pos)

    @staticmethod
    def process_featured_image(file_storage) -> Tuple[BinaryIO, str]:
        """Process featured image, converting to WebP format"""
        return ImageProcessor.convert_to_webp(file_storage, quality=90) 