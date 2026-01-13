"""
RISKCAST Report - Image Exporter
Utilities for processing chart images and base64 conversion
"""

from typing import Optional
import base64
import io
from PIL import Image


class ImageExporter:
    """Image export and processing utilities"""
    
    @staticmethod
    def decode_base64_image(base64_string: str) -> Optional[Image.Image]:
        """
        Decode base64 string to PIL Image
        
        Args:
            base64_string: Base64 encoded image (with or without data URL prefix)
            
        Returns:
            PIL Image object or None if invalid
        """
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',', 1)[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            
            # Create PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for PDF compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else image.split()[1])
                image = rgb_image
            
            return image
            
        except Exception as e:
            print(f"[ImageExporter] Error decoding image: {e}")
            return None
    
    @staticmethod
    def resize_image(image: Image.Image, max_width: int = 800, max_height: int = 600) -> Image.Image:
        """
        Resize image maintaining aspect ratio
        
        Args:
            image: PIL Image object
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            
        Returns:
            Resized PIL Image
        """
        if image.width <= max_width and image.height <= max_height:
            return image
        
        # Calculate new size maintaining aspect ratio
        ratio = min(max_width / image.width, max_height / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
        """
        Convert PIL Image to bytes
        
        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Image bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
    
    @staticmethod
    def process_chart_image(base64_string: str, max_width: int = 800, max_height: int = 600) -> Optional[bytes]:
        """
        Process chart image from base64 for PDF
        
        Args:
            base64_string: Base64 encoded chart image
            max_width: Maximum width for PDF
            max_height: Maximum height for PDF
            
        Returns:
            Image bytes ready for PDF or None if invalid
        """
        image = ImageExporter.decode_base64_image(base64_string)
        if not image:
            return None
        
        # Resize if needed
        image = ImageExporter.resize_image(image, max_width, max_height)
        
        # Convert to bytes
        return ImageExporter.image_to_bytes(image, 'PNG')




















