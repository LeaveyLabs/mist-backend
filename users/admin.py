from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import EmailAuthentication, PhoneNumberAuthentication, PhoneNumberReset, User

class UserAdmin(UserAdmin):
    model = User

class EmailAuthenticationAdmin(admin.ModelAdmin):
    model = EmailAuthentication
    list_display = ("email", "code", "code_time", "validated", "validation_time")

admin.site.register(User, UserAdmin)
admin.site.register(EmailAuthentication, EmailAuthenticationAdmin)
admin.site.register(PhoneNumberAuthentication)
admin.site.register(PhoneNumberReset)