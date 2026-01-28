
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import io

def _load_cv2_image(image_path: str):
    # Handle Korean paths
    img_array = np.fromfile(image_path, np.uint8)
    return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

def _cv2_to_pil(cv_img):
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)

def _pil_to_bytes(pil_img, format='PNG'):
    buf = io.BytesIO()
    pil_img.save(buf, format=format)
    return buf.getvalue()

def process_dual_stream(image_path: str):
    """
    Split image into Molding (Top) and Leadframe (Bottom) with specific enhancements.
    """
    cv_img = _load_cv2_image(image_path)
    if cv_img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    height, width = cv_img.shape[:2]
    split_point = int(height * 0.5)

    # Convert to PIL for easy handling
    pil_img = _cv2_to_pil(cv_img)

    # === 1. Molding (Top Half) ===
    # transforms.Resize((256, 512)) -> H=256, W=512
    # transforms.CenterCrop((254, 320)) -> H=254, W=320
    # Custom Crop (30px from top?) -> "crop_by_pixels(image, 30, 0)"
    
    # Crop Top Half
    top = pil_img.crop((0, 0, width, split_point))
    
    # Resize to (512, 256) (W, H)
    top = top.resize((512, 256), Image.Resampling.BILINEAR)
    
    # Center Crop to (320, 254) (W, H)
    # (Left, Top, Right, Bottom)
    l = (512 - 320) // 2
    t = (256 - 254) // 2
    top = top.crop((l, t, l + 320, t + 254))
    
    # Extra Crop (Simulating crop_by_pixels(30, 0)) -> Crop Top 30px
    # New Size: 320 x (254 - 30) = 320 x 224
    top = top.crop((0, 30, 320, 254))

    # Contrast Enhancement (Factor 2.0)
    enhancer = ImageEnhance.Contrast(top)
    top_enhanced = enhancer.enhance(2.0)
    
    # === 2. Leadframe (Bottom Half) ===
    # Crop Bottom Half
    bot = pil_img.crop((0, split_point, width, height))
    
    # Resize
    bot = bot.resize((512, 256), Image.Resampling.BILINEAR)
    
    # Center Crop
    bot = bot.crop((l, t, l + 320, t + 254))
    
    # Extra Crop (Simulating crop_by_pixels(0, 30)) -> Crop Bottom 30px?? 
    # Or maybe Crop Top 30px relative to the cut?
    # User said "crop_by_pixels(image, 0, 30)". Assuming removing bottom 30px.
    bot = bot.crop((0, 0, 320, 254 - 30))
    
    # Grayscale
    bot_gray = ImageOps.grayscale(bot)
    
    return {
        "molding": _pil_to_bytes(top_enhanced),
        "leadframe": _pil_to_bytes(bot_gray)
    }

if __name__ == "__main__":
    # Test
    res = process_dual_stream("./test/TEST_000.png")
    print(f"Molding bytes: {len(res['molding'])}")
    print(f"Leadframe bytes: {len(res['leadframe'])}")
    
    with open("debug_molding.png", "wb") as f:
        f.write(res['molding'])
    with open("debug_leadframe.png", "wb") as f:
        f.write(res['leadframe'])
    print("Saved debug images.")
