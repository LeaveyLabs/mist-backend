import uuid
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

def get_current_date():
    return datetime.today().date()

def get_current_time():
    return datetime.now().timestamp()

def get_empty_keywords():
    return []

def get_random_email():
    return f'{uuid.uuid4()}@usc.edu'

def get_default_date_of_birth():
    return datetime(2000, 1, 1).date()