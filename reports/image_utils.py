"""
Image preprocessing utilities for improving AI scan quality.
"""
from PIL import Image, ImageEnhance, ImageFilter
import io


def preprocess_image(image_path, output_path=None, max_size=2048, enhance_contrast=True, 
                     sharpen=True, denoise=True):
    """
    Preprocesses an image to improve AI recognition quality.
    
    Args:
        image_path: Path to the input image
        output_path: Optional path to save processed image. If None, overwrites input.
        max_size: Maximum dimension (width or height) for the image
        enhance_contrast: Whether to enhance contrast
        sharpen: Whether to apply sharpening
        denoise: Whether to apply noise reduction
    
    Returns:
        Path to the processed image
    """
    # Open image
    img = Image.open(image_path)
    
    # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 1. Resize if too large (maintains aspect ratio)
    width, height = img.size
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 2. Denoise (reduces grain/noise from phone cameras)
    if denoise:
        img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # 3. Enhance contrast (makes text more readable)
    if enhance_contrast:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)  # 1.3x contrast boost
    
    # 4. Sharpen (improves edge definition for text)
    if sharpen:
        img = img.filter(ImageFilter.SHARPEN)
    
    # Save
    save_path = output_path or image_path
    img.save(save_path, 'JPEG', quality=95, optimize=True)
    
    return save_path


def preprocess_image_bytes(image_bytes, max_size=2048):
    """
    Preprocesses image from bytes and returns processed bytes.
    Useful for in-memory processing without file I/O.
    
    Args:
        image_bytes: Image data as bytes
        max_size: Maximum dimension
    
    Returns:
        Processed image as bytes
    """
    # Open from bytes
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize
    width, height = img.size
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Denoise
    img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    # Convert back to bytes
    output = io.BytesIO()
    img.save(output, 'JPEG', quality=95, optimize=True)
    output.seek(0)
    
    return output.getvalue()
