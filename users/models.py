from datetime import datetime 
import random
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid

class User(AbstractUser):
    picture = models.ImageField(upload_to='profiles', null=True)
    phone_number = PhoneNumberField(null=True)

    class Meta:
        db_table = 'auth_user'

class EmailAuthentication(models.Model):
    def get_random_code():
        return f'{random.randint(0, 999_999):06}'
    
    def get_current_time():
        return datetime.now().timestamp()

    email = models.EmailField()
    code = models.CharField(max_length=6, default=get_random_code, editable=False)
    code_time = models.FloatField(default=get_current_time, editable=False)
    validated = models.BooleanField(default=False)
    validation_time = models.FloatField(null=True)