from rest_framework import permissions
from rest_framework.authtoken.models import Token

from users.generics import get_user_from_request

class UserPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        is_safe_method = request.method in permissions.SAFE_METHODS
        if is_safe_method: return True
        requesting_user = get_user_from_request(request)
        if not requesting_user: return False
        return requesting_user == obj