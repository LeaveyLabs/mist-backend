import os
from push_notifications.models import APNSDevice
import random
from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from sorl.thumbnail import get_thumbnail

from .generics import get_current_time, get_default_date_of_birth, get_empty_prompts, get_random_code, get_random_email

class User(AbstractUser):
    def profile_picture_filepath(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{instance.username}.{ext}'
        return os.path.join('profiles', new_filename)
    
    def confirm_profile_picture_filepath(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{instance.username}.{ext}'
        return os.path.join('confirm-profiles', new_filename)

    def thumbnail_filepath(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{instance.username}.{ext}'
        return os.path.join('thumbnails', new_filename)

    male = 'm'
    female = 'f'
    other = 'o'

    SEXES = (
        (male, male),
        (female, female),
        (other, other),
    )
    MAX_IMAGE_SIZE = (100, 100)
    NUMBER_OF_PROMPTS = 3

    email = models.EmailField(default=get_random_email)
    date_of_birth = models.DateField(default=get_default_date_of_birth)
    picture = models.ImageField(
        upload_to=profile_picture_filepath, default="",
    )
    confirm_picture = models.ImageField(
        upload_to=confirm_profile_picture_filepath, default="",
    )
    thumbnail = models.ImageField(
        upload_to=thumbnail_filepath, default="",
    )
    phone_number = PhoneNumberField(unique=True, null=True)
    sex = models.CharField(max_length=1, choices=SEXES, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    is_verified = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_pending_verification = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    notification_badges_enabled = models.BooleanField(default=False)
    daily_prompts = ArrayField(models.PositiveIntegerField(), size=NUMBER_OF_PROMPTS, default=get_empty_prompts)

    class Meta:
        db_table = 'auth_user'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.picture:
            resized = get_thumbnail(self.picture, '100x100', quality=99)
            self.thumbnail.save(resized.name, ContentFile(resized.read()), False)

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
    phone_number = PhoneNumberField(null=True)
    timestamp = models.FloatField(default=get_current_time)

    def save(self, *args, **kwargs):
        super(Ban, self).save(*args, **kwargs)
        for user in User.objects.filter(phone_number=self.phone_number).all():
            Token.objects.filter(user=user).delete()
            user.is_banned = True
            user.save()

class Notification(models.Model):
    class NotificationTypes:
        TAG = "tag"
        MESSAGE = "message"
        MATCH = "match"
        DAILY_MISTBOX = "dailymistbox"
        MAKE_SOMEONES_DAY = "makesomeonesday"
        COMMENT = "comment"
    
    NOTIFICATION_OPTIONS = (
        (NotificationTypes.MESSAGE, NotificationTypes.MESSAGE),
        (NotificationTypes.TAG, NotificationTypes.TAG),
        (NotificationTypes.DAILY_MISTBOX, NotificationTypes.DAILY_MISTBOX),
        (NotificationTypes.COMMENT, NotificationTypes.COMMENT),
    )

    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    sangdaebang = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=15, choices=NOTIFICATION_OPTIONS,)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    timestamp = models.FloatField(default=get_current_time)
    has_been_seen = models.BooleanField(default=False)

    def update_badges(user):
        badgecount = Notification.objects.\
                        filter(user=user).\
                        exclude(has_been_seen=True).\
                        count()
        if not user.notification_badges_enabled:
            badgecount = 0
        APNSDevice.objects.filter(user=user).\
            send_message(
                None, 
                badge=badgecount,
                extra=None,
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        badgecount = Notification.objects.\
            filter(user=self.user).\
            exclude(has_been_seen=True).\
            count()
        if not self.user.notification_badges_enabled:
            badgecount = 0
        APNSDevice.objects.filter(user=self.user).send_message(
            self.message,
            badge=badgecount,
            extra={
                "type": self.type,
                "data": self.data,
            }
        )