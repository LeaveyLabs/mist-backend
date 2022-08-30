from rest_framework.authtoken.models import Token
from datetime import datetime
import random

def get_user_from_request(request):
    if not request or not request.auth: return None
    matching_tokens = Token.objects.filter(key=request.auth)
    if not matching_tokens: return None
    matching_token = matching_tokens[0]
    return matching_token.user

def get_random_code():
    return f'{random.randint(0, 999_999):06}'

def get_current_time():
    return datetime.now().timestamp()

def get_empty_keywords():
    return []

def is_match(picture, confirm_picture):
    import face_recognition

    if not picture or not confirm_picture: return False

    processed_picture = face_recognition.load_image_file(picture)
    processed_confirm = face_recognition.load_image_file(confirm_picture)
    picture_encodings = face_recognition.face_encodings(processed_picture)
    confirm_encodings = face_recognition.face_encodings(processed_confirm)

    if not picture_encodings: return False
    if not confirm_encodings: return False
    
    results = face_recognition.compare_faces(picture_encodings, confirm_encodings[0])
    return results[0]

def get_face_encoding(picture):
    import face_recognition

    processed_picture = face_recognition.load_image_file(picture)
    picture_encodings = face_recognition.face_encodings(processed_picture)
    
    return picture_encodings