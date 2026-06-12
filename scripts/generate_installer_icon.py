import os
import sys
from PIL import Image

def generate_ico(png_path, ico_path):
    """Generate a multi-size Windows icon (.ico) from a PNG image."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(ico_path), exist_ok=True)
        
        if not os.path.exists(png_path):
            print(f"Error: Source PNG icon not found at {png_path}", file=sys.stderr)
            sys.exit(1)
            
        img = Image.open(png_path)
        
        # Save as ICO with multiple standard dimensions
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(ico_path, format="ICO", sizes=sizes)
        print(f"Successfully generated Windows icon: {ico_path}")
    except Exception as e:
        print(f"Failed to generate icon: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        generate_ico(sys.argv[1], sys.argv[2])
    else:
        generate_ico("assets/images/logo.png", "build/installer/TurboShare.ico")
