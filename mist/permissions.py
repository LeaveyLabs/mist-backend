from rest_framework import permissions
from rest_framework.authtoken.models import Token

def get_token_from_request(request):
    matching_tokens = Token.objects.filter(key=request.auth)
    if not matching_tokens: return None
    matching_token = matching_tokens[0]
    return matching_token

class PostPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            author = request.data.get('author')
            return matching_token.user.pk == author
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.author

class CommentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            author = request.data.get('author')
            return matching_token.user.pk == author
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.author

class VotePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            voter = request.data.get('voter')
            return matching_token.user.pk == voter
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.voter

class FlagPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            flagger = request.data.get('flagger')
            return matching_token.user.pk == flagger
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.flagger

class TagPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            tagging_user = request.data.get('tagging_user')
            return matching_token.user.pk == tagging_user
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.tagging_user

class BlockPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            blocking_user = request.data.get('blocking_user')
            return matching_token.user.pk == blocking_user
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.blocking_user

class MessagePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            matching_token = get_token_from_request(request)
            if not matching_token: return False
            from_user = request.data.get('from_user')
            return matching_token.user.pk == from_user
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_token = get_token_from_request(request)
        if not matching_token: return False
        return matching_token.user == obj.from_user