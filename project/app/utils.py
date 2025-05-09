import uuid
import os
from app import app
from PIL import Image

def save_picture(form_picture, filename_override=None):
    import secrets, os
    from PIL import Image

    if filename_override:
        picture_fn = filename_override
    else:
        random_hex = secrets.token_hex(16)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext

    picture_path = os.path.join(app.root_path, 'static/profile_pictures', picture_fn)
    output_size = (300, 300)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def save_file_upload(form_file_upload, filename_override=None):
    import os

    # Create directory if it doesn't exist
    upload_dir = os.path.join(app.root_path, 'static/file_uploads')
    os.makedirs(upload_dir, exist_ok=True)

    try:
        
        original_filename = form_file_upload.filename

        if filename_override:
            file_upload_fn = filename_override
        else:
            # Use UUID for unique filename
            _, f_ext = os.path.splitext(original_filename)
            file_upload_fn = str(uuid.uuid4()) + f_ext

        file_path = os.path.join(upload_dir, file_upload_fn)
        form_file_upload.save(file_path)
        
        return file_upload_fn, original_filename
    except Exception as e:
        app.logger.error(f"Error saving file upload: {e}")
        raise