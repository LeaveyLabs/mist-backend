from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
from .models import EmailAuthentication, PhoneNumberAuthentication, PhoneNumberReset, User

class UserAdmin(UserAdmin):
    model = User
    list_display = ("id", "email", "first_name", "last_name", "token")

    def token(self, obj):
        key, _ = Token.objects.get_or_create(user_id=obj.id)
        return key

class EmailAuthenticationAdmin(admin.ModelAdmin):
    model = EmailAuthentication
    list_display = ("email", "code", "code_time", "validated", "validation_time")

admin.site.register(User, UserAdmin)
admin.site.register(EmailAuthentication, EmailAuthenticationAdmin)
admin.site.register(PhoneNumberAuthentication)
admin.site.register(PhoneNumberReset)