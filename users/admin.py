from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
from .models import EmailAuthentication, PhoneNumberAuthentication, PhoneNumberReset, User

ADDITIONAL_USER_FIELDS = (
    (None, {'fields': ('phone_number', 'date_of_birth', 'is_hidden')}),
)

class UserAdmin(UserAdmin):
    model = User
    list_display = ("id", "email", "first_name", "last_name", "token", "phone_number")

    add_fieldsets = UserAdmin.add_fieldsets + ADDITIONAL_USER_FIELDS
    fieldsets = UserAdmin.fieldsets + ADDITIONAL_USER_FIELDS

    def token(self, obj):
        key, _ = Token.objects.get_or_create(user_id=obj.id)
        return key

class EmailAuthenticationAdmin(admin.ModelAdmin):
    model = EmailAuthentication
    list_display = ("email", "code", "code_time", "validated", "validation_time")

class PhoneNumberAuthenticationAdmin(admin.ModelAdmin):
    model = PhoneNumberAuthentication
    list_display = ("email", "phone_number", "code", "code_time", "validated", "validation_time")

class PhoneNumberResetAdmin(admin.ModelAdmin):
    model = PhoneNumberReset
    list_display = ("email", "email_code", "email_code_time", "phone_number", "phone_number_code", "phone_number_code_time", "phone_number_validated")

admin.site.register(User, UserAdmin)
admin.site.register(EmailAuthentication, EmailAuthenticationAdmin)
admin.site.register(PhoneNumberAuthentication, PhoneNumberAuthenticationAdmin)
admin.site.register(PhoneNumberReset, PhoneNumberResetAdmin)