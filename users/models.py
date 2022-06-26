from datetime import datetime 
from django.contrib.auth.models import AbstractUser
from django.db import models
import os
from phonenumber_field.modelfields import PhoneNumberField
import random

class User(AbstractUser):
    def profile_picture_filepath(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{instance.id}.{ext}'
        return os.path.join('profiles', new_filename)

    male = 'm'
    female = 'f'
    SEXES = (
        (male, male),
        (female, female),
    )

    date_of_birth = models.DateField()
    picture = models.ImageField(upload_to=profile_picture_filepath, null=True)
    phone_number = PhoneNumberField(null=True)
    sex = models.CharField(max_length=1, choices=SEXES, null=True)

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

class PasswordReset(models.Model):
    def get_random_code():
        return f'{random.randint(0, 999_999):06}'

    def get_current_time():
        return datetime.now().timestamp()

    email = models.EmailField()
    code = models.CharField(max_length=6, default=get_random_code, editable=False)
    code_time = models.FloatField(default=get_current_time, editable=False)
    validated = models.BooleanField(default=False)
    validation_time = models.FloatField(null=True)