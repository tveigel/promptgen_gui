from PIL import Image
import os

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(script_dir):
    if filename.lower().endswith(".png"):
        filepath = os.path.join(script_dir, filename)

        with Image.open(filepath) as img:
            # Ensure image has alpha channel
            img = img.convert("RGBA")

            # Resize to 30x30
            resized_img = img.resize((12, 12), Image.Resampling.LANCZOS)

            # Create a new transparent image with size 30x32
            new_img = Image.new("RGBA", (12, 14), (0, 0, 0, 0))

            # Paste resized image 2 pixels down
            new_img.paste(resized_img, (0, 2))

            new_img.save(filepath)

print("All PNGs resized to 30x30 and padded to 30x32 with transparency.")
