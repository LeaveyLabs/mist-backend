from rest_framework import permissions
from mist.models import FriendRequest
from users.generics import get_user_from_request

def requested_user_is_the_posted_user(request, user_property):
    requesting_user = get_user_from_request(request)
    posted_user = request.data.get(user_property)
    if not requesting_user or not posted_user: return False 
    posted_user_pk = int(posted_user)
    return requesting_user.pk == posted_user_pk


def requested_user_is_the_queried_user(request, user_property):
    requesting_user = get_user_from_request(request)
    posted_user = request.query_params.get(user_property)
    if not requesting_user or not posted_user: return False 
    posted_user_pk = int(posted_user)
    return requesting_user.pk == posted_user_pk


class PostPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            requesting_user = get_user_from_request(request)
            if not requesting_user: return False
            if not request.query_params.get('author'): return True
            author_pk = int(request.query_params.get('author'))
            if requesting_user.pk == author_pk: return True
            user_friend_requested_author = FriendRequest.objects.filter(
                friend_requesting_user_id=requesting_user.pk,
                friend_requested_user_id=author_pk,
            )
            author_friend_requested_user = FriendRequest.objects.filter(
                friend_requesting_user_id=author_pk,
                friend_requested_user_id=requesting_user.pk,
            )
            user_and_author_are_friends = (user_friend_requested_author and 
                                            author_friend_requested_user)
            return user_and_author_are_friends
        elif request.method == "POST":
            return requested_user_is_the_posted_user(request, 'author')
        return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.author

class CommentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return requested_user_is_the_posted_user(request, 'author')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.author

class VotePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return requested_user_is_the_posted_user(request, 'voter')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.voter

class FlagPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return requested_user_is_the_posted_user(request, 'flagger')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.flagger

class TagPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return requested_user_is_the_posted_user(request, 'tagging_user')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.tagging_user

class BlockPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return requested_user_is_the_posted_user(request, 'blocking_user')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.blocking_user

class MessagePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            user_is_sender = requested_user_is_the_queried_user(request, 'sender')
            user_is_receiver = requested_user_is_the_queried_user(request, 'receiver')
            return user_is_sender or user_is_receiver
        elif request.method == "POST":
            return requested_user_is_the_posted_user(request, 'sender')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.sender

class FriendRequestPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            user_is_sender = requested_user_is_the_queried_user(request, 'friend_requesting_user')
            user_is_receiver = requested_user_is_the_queried_user(request, 'friend_requested_user')
            return user_is_sender or user_is_receiver
        elif request.method == "POST":
            return requested_user_is_the_posted_user(request, 'friend_requesting_user')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.friend_requesting_user
    
class FavoritePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return requested_user_is_the_posted_user(request, 'favoriting_user')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.favoriting_user

class MatchRequestPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            user_is_sender = requested_user_is_the_queried_user(request, 'match_requesting_user')
            user_is_receiver = requested_user_is_the_queried_user(request, 'match_requested_user')
            return user_is_sender or user_is_receiver
        elif request.method == "POST":
            return requested_user_is_the_posted_user(request, 'match_requesting_user')
        else:
            return True

    def has_object_permission(self, request, view, obj):
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.match_requesting_user