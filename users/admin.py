from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import EmailAuthentication, PhoneNumberAuthentication, PhoneNumberReset, User

class UserAdmin(UserAdmin):
    model = User

admin.site.register(User, UserAdmin)
admin.site.register(EmailAuthentication)
admin.site.register(PhoneNumberAuthentication)
admin.site.register(PhoneNumberReset)