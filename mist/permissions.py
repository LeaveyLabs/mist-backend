from rest_framework import permissions
from users.generics import get_user_from_request

class PostPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            requesting_user = get_user_from_request(request)
            author_pk = request.data.get('author')
            if not requesting_user: return False
            return requesting_user.pk == author_pk
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.author

class CommentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            requesting_user = get_user_from_request(request)
            author_pk = request.data.get('author')
            if not requesting_user: return False
            return requesting_user.pk == author_pk
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
            requesting_user = get_user_from_request(request)
            voter_pk = request.data.get('voter')
            if not requesting_user: return False
            return requesting_user.pk == voter_pk
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.voter

class FlagPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            requesting_user = get_user_from_request(request)
            flagger_pk = request.data.get('flagger')
            if not requesting_user: return False
            return requesting_user.pk == flagger_pk
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.flagger

class TagPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            requesting_user = get_user_from_request(request)
            tagging_user_pk = request.data.get('tagging_user')
            if not requesting_user: return False
            return requesting_user.pk == tagging_user_pk
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
            requesting_user = get_user_from_request(request)
            blocking_user_pk = request.data.get('blocking_user')
            if not requesting_user: return False
            return requesting_user.pk == blocking_user_pk
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.blocking_user

class MessagePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            requesting_user = get_user_from_request(request)
            from_user_pk = request.data.get('from_user')
            if not requesting_user: return False
            return requesting_user.pk == from_user_pk
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.from_user

class FriendRequestPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            requesting_user = get_user_from_request(request)
            friend_requesting_user_pk = request.data.get('friend_requesting_user')
            if not requesting_user: return False
            return requesting_user.pk == friend_requesting_user_pk
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj.friend_requesting_user