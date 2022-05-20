from rest_framework import permissions
from rest_framework.authtoken.models import Token

class UserPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        matching_tokens = Token.objects.filter(key=request.auth)
        if not matching_tokens: return False
        matching_token = matching_tokens[0]
        return matching_token.user == obj