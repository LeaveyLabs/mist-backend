from rest_framework import permissions
from rest_framework.authtoken.models import Token


class TestPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return True

# class SampleModelPermissions(permissions.DjangoObjectPermissions):
