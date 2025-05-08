import os
import secrets
from PIL import Image
from app import app

def save_picture(form_picture):
    # Generate random filename to avoid conflicts
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + f_ext
    
    # Ensure directory exists
    picture_dir = os.path.join(app.root_path, 'static/profile_pictures')
    if not os.path.exists(picture_dir):
        os.makedirs(picture_dir)
        
    picture_path = os.path.join(picture_dir, picture_filename)
    
    # Resize image to save space and load time
    output_size = (256, 256)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    # Save the image
    i.save(picture_path)
    
    # Return the filename so it can be stored in the database
    return picture_filename