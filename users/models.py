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
    email = models.EmailField()
    code = models.CharField(max_length=6)
    code_time = models.FloatField()
    validated = models.BooleanField(default=False)
    validation_time = models.FloatField(null=True)