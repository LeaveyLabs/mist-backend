from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
import random
import string

# Generic String Methods
def random_string(chars = string.ascii_lowercase, length=10):
    return ''.join(random.choice(chars) for _ in range(length))

# HTTP Methods
class HttpMethods(Enum):
    GET = 0
    POST = 1
    PUT = 2
    PATCH = 3
    DELETE = 4

# API Throttle Checks
def api_throttled_or_valid_json(client, endpoint, headers, 
    validator, data=None, method=HttpMethods.GET, files=None):

    request_method = None
    if method == HttpMethods.GET:
        request_method = client.get
    elif method == HttpMethods.POST:
        request_method = client.post
    elif method == HttpMethods.PUT:
        request_method = client.put
    elif method == HttpMethods.PATCH:
        request_method = client.patch
    elif method == HttpMethods.DELETE:
        request_method = client.delete

    with request_method(
        endpoint,
        data=data,
        headers=headers, 
        catch_response=True,
        files=files) as response:
        
        if response.status_code == HTTPStatus.TOO_MANY_REQUESTS: 
            response.success()
            return None
        elif not 200 <= response.status_code <= 299:
            print(response.content)
            return None
        elif method == HttpMethods.DELETE:
            return None
        elif not validator(response.json()):
            response.failure("Despite status code, invalid JSON was returned.")

        return response.json()

# Test Entities
@dataclass
class User:
    id: int
    token: str

# JSON Validators
def properties_in_obj(obj, properties):
    for property in properties:
        if property not in obj:
            print(f"Object is missing {property}")
            return False
    return True

def is_anything(anything):
    return True

def is_friend_request(friend_request):
    return properties_in_obj(
        friend_request,
        ('id', 'friend_requesting_user', 'friend_requested_user',)
    )

def is_match_request(match_request):
    return properties_in_obj(
        match_request,
        ('id', 'match_requesting_user', 'match_requested_user',)
    )

def is_favorite(favorite):
    return properties_in_obj(
        favorite,
        ('id', 'favoriting_user', 'post',)
    )

def is_block(block):
    return properties_in_obj(
        block,
        ('id', 'blocking_user', 'blocked_user',)
    )

def is_flag(flag):
    return properties_in_obj(
        flag, 
        ('id', 'flagger', 'post',)
    )

def is_vote(vote):
    return properties_in_obj(
        vote, 
        ('id', 'voter', 'post',)
    )

def is_message(message):
    return properties_in_obj(
        message, 
        ('id', 'body', 'sender', 'receiver', 'timestamp',)
    )

def is_read_only_user(user):
    return properties_in_obj(
        user, 
        ('id', 'username', 'first_name', 'last_name',)
    )

def is_post(post):
    return properties_in_obj(
        post,
        ('id', 'title', 'body', 'timestamp', 'author',)
    )

def is_comment(comment):
    return properties_in_obj(
        comment,
        ('id', 'body', 'timestamp', 'post', 'author',)
    )

def is_user_id(user_id):
    try:
        return int(user_id)
    except:
        return False

def is_word(word):
    return properties_in_obj(
        word,
        ('id', 'text', 'occurrences')
    )

def is_success(response):
    return response["type"] == "success"

def is_throttled(response):
    return "throttled" in str(response)

def is_message_response(response):
    return properties_in_obj(
        response,
        ('type', 'sender', 'receiver', 'body', 'timestamp')
    )

def contains_valid_entities(objects, validator):
    for object in objects:
        if not validator(object):
            return False
    return True

def contains_messages(messages):
    return contains_valid_entities(messages, is_message)

def contains_read_only_users(users):
    return contains_valid_entities(users, is_read_only_user)

def contains_posts(posts):
    return contains_valid_entities(posts, is_post)

def contains_comments(comments):
    return contains_valid_entities(comments, is_comment)

def contains_conversations(conversations):
    for user_id in conversations:
        if not is_user_id(user_id):
            return False
        if not contains_messages(conversations[user_id]):
            return False
    return True

def contains_votes(votes):
    return contains_valid_entities(votes, is_vote)

def contains_flags(flags):
    return contains_valid_entities(flags, is_flag)

def contains_blocks(blocks):
    return contains_valid_entities(blocks, is_block)

def contains_favorites(favorites):
    return contains_valid_entities(favorites, is_favorite)

def contains_match_requests(match_requests):
    return contains_valid_entities(match_requests, is_match_request)

def contains_friend_requests(friend_requests):
    return contains_valid_entities(friend_requests, is_friend_request)

def contains_words(words):
    return contains_valid_entities(words, is_word)