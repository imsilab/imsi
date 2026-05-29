import os
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(r"c:\Users\임준수\Desktop\imsi_capp")
logo_path = ROOT / "images" / "logo" / "main-logo.png"

# Target paths to overwrite
png_targets = {
    32: [
        ROOT / "images" / "imsi_favicon_32.png",
        ROOT / "_site" / "images" / "imsi_favicon_32.png",
        ROOT / "images" / "icon_hu027d87ac1e37f4f802995042c9999554_21044_32x32_fill_lanczos_center_2.png",
        ROOT / "_site" / "images" / "icon_hu027d87ac1e37f4f802995042c9999554_21044_32x32_fill_lanczos_center_2.png",
        ROOT / "img" / "icon-32.png",
        ROOT / "_site" / "img" / "icon-32.png",
    ],
    192: [
        ROOT / "images" / "imsi_favicon_192.png",
        ROOT / "_site" / "images" / "imsi_favicon_192.png",
        ROOT / "images" / "icon_hu027d87ac1e37f4f802995042c9999554_21044_192x192_fill_lanczos_center_2.png",
        ROOT / "_site" / "images" / "icon_hu027d87ac1e37f4f802995042c9999554_21044_192x192_fill_lanczos_center_2.png",
        ROOT / "img" / "icon-192.png",
        ROOT / "_site" / "img" / "icon-192.png",
    ],
    512: [
        ROOT / "images" / "imsi_favicon_512.png",
        ROOT / "_site" / "images" / "imsi_favicon_512.png",
        ROOT / "images" / "icon_hu027d87ac1e37f4f802995042c9999554_21044_512x512_fill_lanczos_center_2.png",
        ROOT / "_site" / "images" / "icon_hu027d87ac1e37f4f802995042c9999554_21044_512x512_fill_lanczos_center_2.png",
        ROOT / "img" / "icon-512.png",
        ROOT / "_site" / "img" / "icon-512.png",
    ]
}

ico_targets = [
    ROOT / "favicon.ico",
    ROOT / "_site" / "favicon.ico",
    ROOT / "img" / "favicon.ico",
    ROOT / "_site" / "img" / "favicon.ico"
]

def make_square_logo(src_img, size, padding_ratio=0.1):
    # Find bounding box of logo contents (excluding the white background)
    rgb_img = src_img.convert("RGB")
    inverted = ImageOps.invert(rgb_img)
    bbox = inverted.getbbox()
    if bbox:
        cropped = src_img.crop(bbox)
    else:
        cropped = src_img

    # Create solid white square canvas
    canvas = Image.new("RGB", (size, size), "white")
    
    # Calculate fit size with padding
    pad = int(size * padding_ratio)
    max_w = size - 2 * pad
    max_h = size - 2 * pad
    
    # Maintain aspect ratio
    orig_w, orig_h = cropped.size
    ratio = min(max_w / orig_w, max_h / orig_h)
    new_w = int(orig_w * ratio)
    new_h = int(orig_h * ratio)
    
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Paste centered
    offset_x = (size - new_w) // 2
    offset_y = (size - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))
    
    return canvas

def main():
    if not logo_path.exists():
        print(f"Error: Main logo not found at {logo_path}")
        return

    print("Loading main logo...")
    logo = Image.open(logo_path)
    
    # Save PNG versions
    for size, paths in png_targets.items():
        print(f"Generating square logo for size {size}...")
        square_img = make_square_logo(logo, size, padding_ratio=0.1)
        for p in paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            square_img.save(p, "PNG")
            print(f"Saved: {p.relative_to(ROOT)}")
            
    # Generate and save ICO versions
    print("Generating multi-size ICO file...")
    # ICO uses multiple sizes, typically 16, 32, 48, 64
    ico_sizes = [16, 32, 48, 64]
    ico_images = [make_square_logo(logo, s, padding_ratio=0.08) for s in ico_sizes]
    
    for p in ico_targets:
        p.parent.mkdir(parents=True, exist_ok=True)
        # Pillow saves multi-size ICO using the first image and passing secondary images to append_images
        ico_images[0].save(p, format="ICO", sizes=[(s, s) for s in ico_sizes], append_images=ico_images[1:])
        print(f"Saved ICO: {p.relative_to(ROOT)}")
        
    print("All favicons and share preview assets generated successfully!")

if __name__ == "__main__":
    main()
