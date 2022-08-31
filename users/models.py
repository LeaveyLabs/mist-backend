from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from .generics import get_current_time, get_empty_keywords, get_random_code
import os
from phonenumber_field.modelfields import PhoneNumberField
import random

class User(AbstractUser):
    def profile_picture_filepath(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{instance.id}.{ext}'
        return os.path.join('profiles', new_filename)
    
    def confirm_profile_picture_filepath(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{instance.id}.{ext}'
        return os.path.join('confirm-profiles', new_filename)

    male = 'm'
    female = 'f'
    other = 'o'

    SEXES = (
        (male, male),
        (female, female),
        (other, other),
    )
    NUMBER_OF_KEYWORDS = 5

    date_of_birth = models.DateField()
    picture = models.ImageField(
        upload_to=profile_picture_filepath, null=True, blank=True
    )
    confirm_picture = models.ImageField(
        upload_to=confirm_profile_picture_filepath, null=True, blank=True
    )
    phone_number = PhoneNumberField(null=True, unique=True)
    sex = models.CharField(max_length=1, choices=SEXES, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    keywords = ArrayField(models.TextField(), size=NUMBER_OF_KEYWORDS, default=get_empty_keywords)
    is_verified = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_user'

class EmailAuthentication(models.Model):
    def get_random_code():
        return f'{random.randint(0, 999_999):06}'

    def get_current_time():
        return datetime.now().timestamp()
        
    email = models.EmailField(unique=True)
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

class PhoneNumberAuthentication(models.Model):
    email = models.EmailField(default='', blank=True)
    phone_number = PhoneNumberField(unique=True)
    code = models.CharField(max_length=6, default=get_random_code)
    code_time = models.FloatField(default=get_current_time)
    validated = models.BooleanField(default=False)
    validation_time = models.FloatField(null=True)

class PhoneNumberReset(models.Model):
    email = models.EmailField(unique=True)
    email_code = models.CharField(max_length=6, default=get_random_code)
    email_code_time = models.FloatField(default=get_current_time)
    email_validated = models.BooleanField(default=False)
    email_validation_time = models.FloatField(null=True)

    reset_token = models.CharField(max_length=6, default=get_random_code)

    phone_number = PhoneNumberField(unique=True, null=True)
    phone_number_code = models.CharField(max_length=6, default=get_random_code)
    phone_number_code_time = models.FloatField(default=get_current_time)
    phone_number_validated = models.BooleanField(default=False)
    phone_number_validation_time = models.FloatField(null=True)

class Ban(models.Model):
    email = models.EmailField(unique=True)
    timestamp = models.FloatField(default=get_current_time)

    def save(self, *args, **kwargs):
        super(Ban, self).save(*args, **kwargs)
        User.objects.filter(email__iexact=self.email).delete()