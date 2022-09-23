def gen_phone():
    import random

    last = (str(random.randint(1,9998)).zfill(4))
    while last in ['1111','2222','3333','4444','5555','6666','7777','8888']:
        last = (str(random.randint(1,9998)).zfill(4))
        
    return f'+1310310{last}'

def create_dummy_user_and_token_given_id(id):
    from datetime import date
    from users.models import User
    from rest_framework.authtoken.models import Token

    username_handle = f'testuser{id}'

    user = User.objects.create(
        email=f'{username_handle}@usc.edu',
        username=username_handle,
        date_of_birth=date(2000, 1, 1),
        phone_number=gen_phone(),
        notification_badges_enabled=True,
    )

    token = Token.objects.create(user=user)

    return (user, token)

def create_simple_uploaded_file_from_image_path(image_path, new_file_name):
    from PIL import Image
    from io import BytesIO
    from django.core.files.uploadedfile import SimpleUploadedFile

    image = Image.open(image_path)
    image_io = BytesIO()
    image.save(image_io, format='JPEG')

    return SimpleUploadedFile(new_file_name, image_io.getvalue(), content_type='image/jpeg')

