from PIL import Image, ImageDraw, ImageFont
import time

def generate_meme(top_text, bottom_text, template_path='drake_meme_template.jpg'):
    try:
        im = Image.open(template_path)
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("arial.ttf", 40)  # Adjust font/size as needed
        
        # Calculate text positions (centered for simplicity)
        width, height = im.size
        top_bbox = draw.textbbox((0, 0), top_text, font=font)
        top_width = top_bbox[2] - top_bbox[0]
        draw.text(((width - top_width) / 2, 10), top_text, (0, 0, 0), font=font)
        
        bottom_bbox = draw.textbbox((0, 0), bottom_text, font=font)
        bottom_width = bottom_bbox[2] - bottom_bbox[0]
        draw.text(((width - bottom_width) / 2, height - bottom_bbox[3] - 10), bottom_text, (0, 0, 0), font=font)
        
        meme_path = f"meme_{int(time.time())}.jpg"
        im.save(meme_path)
        return meme_path
    except FileNotFoundError:
        raise Exception("Meme template or font not found. Ensure 'drake_meme_template.jpg' and 'arial.ttf' are available.")