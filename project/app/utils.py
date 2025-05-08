import uuid
import os
from app import app
from PIL import Image

def save_picture(form_picture, filename_override=None, return_filename_only=False):
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

    if return_filename_only:
        return picture_fn
    return picture_fn