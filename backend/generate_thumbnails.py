import os
from pathlib import Path
from PIL import Image

def generate_thumbnail(image_path: Path, max_size: int = 300) -> Path:
    """Generate a thumbnail for an image if it doesn't exist"""
    try:
        # Create thumbnails directory if it doesn't exist
        thumb_dir = Path("static/images/thumbnails")
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail filename
        thumb_name = image_path.stem + "_thumb" + image_path.suffix
        thumb_path = thumb_dir / thumb_name
        
        # If thumbnail already exists, return its path
        if thumb_path.exists():
            print(f"Thumbnail already exists: {thumb_path}")
            return thumb_path
            
        print(f"Generating thumbnail for: {image_path}")
        # Open and resize image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, 'white')
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            ratio = max_size / max(img.size)
            if ratio < 1:
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumb_path, quality=85, optimize=True)
            print(f"Generated thumbnail: {thumb_path}")
            return thumb_path
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None

def main():
    images_dir = Path("static/images")
    if not images_dir.exists():
        print(f"Images directory not found: {images_dir}")
        return

    # Process all images
    for file_path in images_dir.glob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
            generate_thumbnail(file_path)

if __name__ == "__main__":
    main()