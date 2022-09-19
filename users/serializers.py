from datetime import date, datetime, timedelta
import re
from django.forms import ValidationError
# from profanity_check import predict
from rest_framework import serializers
from mist.models import Badge, Mistbox
from mist_worker.tasks import verify_profile_picture_task

from users.generics import get_current_time
from .models import Ban, PhoneNumberAuthentication, PhoneNumberReset, User, EmailAuthentication
from phonenumber_field.serializerfields import PhoneNumberField

class ReadOnlyUserSerializer(serializers.ModelSerializer):
    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 
        'picture', 'is_verified', 'badges', 'thumbnail',)
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 
        'picture', 'is_verified', 'badges', 'thumbnail',)

    def get_badges(self, obj):
        badges = []
        try: badges = obj.badges
        except: badges = Badge.objects.filter(user_id=obj.id)
        return [badge.badge_type for badge in badges.all()]

class CompleteUserSerializer(serializers.ModelSerializer):
    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()
    MEGABYTE_LIMIT = 10

    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username',
        'first_name', 'last_name', 'picture',
        'confirm_picture', 'phone_number',
        'date_of_birth', 'sex', 'latitude', 'longitude',
        'is_verified', 'is_pending_verification', 'badges',
        'is_superuser', 'thumbnail',)
        read_only_fields = ('badges', 'is_verified', 'is_pending_verification',)
        extra_kwargs = {
            'picture': {'required': True},
            'phone_number': {'required': True},
        }
    
    def get_badges(self, obj):
        badges = []
        try: badges = obj.badges
        except: badges = Badge.objects.filter(user_id=obj.id)
        return [badge.badge_type for badge in badges.all()]
    
    def email_matches_name(email, first_name, last_name):
        first_name_in_email = email.find(first_name) != -1
        last_name_in_email = email.find(last_name) != -1
        return first_name_in_email or last_name_in_email

    def picture_below_size_limit(self, picture):
        filesize = picture.size
        return filesize > self.MEGABYTE_LIMIT * 1024 * 1024

    def validate_username(self, username):
        alphanumeric_dash_and_underscores_only = "^[A-Za-z0-9_-]*$"
        if not re.match(alphanumeric_dash_and_underscores_only, username):
            raise ValidationError("abc, 123, _ and .")
        # [is_offensive] = predict([username])
        # if is_offensive:
        #     raise serializers.ValidationError("Avoid offensive language")
        return username.lower()

    def validate_first_name(self, first_name):
        letters_only = "^[A-Za-z]*$"
        if not re.match(letters_only, first_name):
            raise ValidationError("Letters only")
        # [is_offensive] = predict([first_name])
        # if is_offensive:
        #     raise serializers.ValidationError("Avoid offensive language")
        return first_name

    def validate_last_name(self, last_name):
        letters_only = "^[A-Za-z]*$"
        if not re.match(letters_only, last_name):
            raise ValidationError("Letters only")
        # [is_offensive] = predict([last_name])
        # if is_offensive:
        #     raise serializers.ValidationError("Avoid offensive language")
        return last_name
    
    def validate_date_of_birth(self, date_of_birth):
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        if age < 18:
            raise ValidationError("Users must be over 18 years old")
        return date_of_birth
    
    # def validate_email(self, email):
    #     users_with_matching_email = User.objects.filter(email__iexact=email)
    #     if users_with_matching_email:
    #         raise ValidationError("Email is already registered")
    #     email_is_banned = Ban.objects.filter(email__iexact=email)
    #     if email_is_banned:
    #          raise ValidationError("Email's been banned")
    #     return email

    def validate_picture(self, picture):
        if self.picture_below_size_limit(picture):
            raise ValidationError(f"Max file size is {self.MEGABYTE_LIMIT}MB")
        return picture

    # def verify_email_authentication(self, validated_data):
    #     email = validated_data.get('email').lower()
    #     validations_with_matching_email = EmailAuthentication.objects.filter(
    #         email__iexact=email)
    #     email_auth_requests = validations_with_matching_email.order_by('-validation_time')

    #     if not email_auth_requests:
    #         raise serializers.ValidationError({"email": "Email was not registered"})

    #     most_recent_auth_request = email_auth_requests[0]

    #     if not most_recent_auth_request.validated:
    #         raise serializers.ValidationError({"email": "Email was not validated"})

    #     current_time = datetime.now().timestamp()
    #     time_since_validation = current_time - most_recent_auth_request.validation_time
    #     validation_expired = time_since_validation > self.EXPIRATION_TIME

    #     if validation_expired:
    #         raise serializers.ValidationError({"email": "Email validation expired"})

    #     users_with_matching_email = User.objects.filter(email__iexact=email)
    #     if len(users_with_matching_email):
    #         raise serializers.ValidationError({"email": "Email already taken"})
    
    def verify_phone_number(self, validated_data):
        # email = validated_data.get('email')
        phone_number = validated_data.get('phone_number')

        # if not email:
        #     raise serializers.ValidationError({"email": "Email was not registered"})

        if not phone_number:
            raise serializers.ValidationError({"phone_number": "Phone number was not registered"})
        
        # email = email.lower()
        phone_number = phone_number.lower()
        
        matching_validations = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number)

        if not matching_validations:
            raise serializers.ValidationError({"phone_number": "Phone number was not registered"})

        most_recent_auth_request = matching_validations[0]

        if not most_recent_auth_request.validated:
            raise serializers.ValidationError({"phone_number": "Phone number was not validated"})

        current_time = datetime.now().timestamp()
        time_since_validation = current_time - most_recent_auth_request.validation_time
        validation_expired = time_since_validation > self.EXPIRATION_TIME

        if validation_expired:
            raise serializers.ValidationError({"phone_number": "Phone number validation expired"})

        users_with_matching_phone_number = User.objects.filter(phone_number=phone_number)
        if len(users_with_matching_phone_number):
            raise serializers.ValidationError({"phone_number": "Phone number already taken"})

    def verify_username(self, validated_data):
        username = validated_data.get('username').lower()

        if not username:
            raise ValidationError({"username": "Username was not provided"})

        alphanumeric_dash_period_and_underscores_only = "^[A-Za-z0-9_\.]*$"
        if not re.match(alphanumeric_dash_period_and_underscores_only, username):
            raise ValidationError({"username": "abc, 123, _ and . only"})

        users_with_matching_username = User.objects.filter(username__iexact=username)
        if users_with_matching_username:
            raise ValidationError({"username": "Username is not unique"})

    def create(self, validated_data):
        # self.verify_email_authentication(validated_data)
        self.verify_phone_number(validated_data)
        self.verify_username(validated_data)
        user = User.objects.create(**validated_data)
        user.set_unusable_password()
        user.save()
        return user

    def start_verify_profile_picture_task(self, instance):
        from backend import celery_app
        celery_app.send_task(name="verify_profile_picture_task", args=[instance.id])
    
    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email).lower()
        instance.username = validated_data.get('username', instance.username).lower()
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.latitude = validated_data.get('latitude', instance.latitude)
        instance.longitude = validated_data.get('longitude', instance.longitude)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.picture = validated_data.get('picture', instance.picture)
        instance.confirm_picture = validated_data.get('confirm_picture', instance.confirm_picture)
        instance.save()
        if instance.picture and instance.confirm_picture:
            instance.is_pending_verification = True
            self.start_verify_profile_picture_task(instance)
        else:
            instance.is_pending_verification = False
            instance.is_verified = False
        instance.save()
        return instance
    
    def partial_update(self, instance, validated_data):
        return self.update(self, instance, validated_data)

class UserEmailRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    ACCEPTABLE_DOMAINS = ('usc.edu', )
    
    def validate_email(self, email):
        lowercased_email = email.lower()

        users_with_matching_email = User.objects.filter(email__iexact=lowercased_email)
        if users_with_matching_email:
            raise ValidationError("Email is already registered")

        email_is_banned = Ban.objects.filter(email__iexact=lowercased_email)
        if email_is_banned:
            raise ValidationError("Email's been banned")

        domain = email.split('@')[1]
        if domain not in self.ACCEPTABLE_DOMAINS:
            raise ValidationError("Email has an invalid domain")

        return lowercased_email

class UserEmailValidationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        email = data.get('email').lower()
        registrations_with_matching_email = EmailAuthentication.objects.filter(
                email__iexact=email).order_by('-code_time')

        if not registrations_with_matching_email:
            raise ValidationError({"email": "Email's not registered"})

        code = data.get('code')
        registration = registrations_with_matching_email[0]
        if code != registration.code:
            raise ValidationError({"code": "Code doesn't match"})

        current_time = datetime.now().timestamp()
        time_since_registration = current_time - registration.code_time 
        registration_expired = time_since_registration > self.EXPIRATION_TIME

        if registration_expired:
            raise ValidationError({"code": "Expired code"})

        return data

class UsernameValidationRequestSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, username):
        alphanumeric_dash_period_and_underscores_only = "^[A-Za-z0-9_\.]*$"
        if not re.match(alphanumeric_dash_period_and_underscores_only, username):
            raise ValidationError("abc, 123, _ and . only")

        users_with_matching_username = User.objects.filter(username__iexact=username)
        if users_with_matching_username:
            raise ValidationError("Username's taken")
        
        # [is_offensive] = predict([username])
        # if is_offensive:
        #     raise serializers.ValidationError("Avoid offensive language")

        return username

class PhoneNumberRegistrationSerializer(serializers.Serializer):
    # email = serializers.EmailField()
    phone_number = PhoneNumberField()

    EXPIRATION_TIME = timedelta(minutes=0).total_seconds()

    # def validate(self, data):
    #     # email = data.get('email').lower()
    #     phone_number = data.get('phone_number')

    #     matching_regsitrations = PhoneNumberAuthentication.objects.filter(
    #         phone_number=phone_number,
    #     ).order_by('-code_time')

    #     if not matching_regsitrations:
    #         return data
        
    #     matching_regsitration = matching_regsitrations[0]

        # current_time = datetime.now().timestamp()
        # time_since_registration = current_time - matching_regsitration.code_time
        # registration_expired = time_since_registration > self.EXPIRATION_TIME

        # if not registration_expired:
        #     raise ValidationError({"phone_number": "Phone's being registered by someone else"})

        # return data

    def validate_email(self, email):
        matching_emails = User.objects.filter(email__iexact=email)
        if matching_emails:
            raise ValidationError("Email is already in use")
        return email
    
    def validate_phone_number(self, phone_number):
        matching_phone_numbers = User.objects.filter(phone_number=phone_number)
        if matching_phone_numbers:
            raise ValidationError("Phone number is in use")
        return phone_number

class LoginCodeRequestSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()

    def validate_phone_number(self, phone_number):
        matching_users = User.objects.filter(phone_number=phone_number)
        if not matching_users:
            raise ValidationError("User does not exist")
        matching_user = matching_users[0]
        if matching_user.is_banned:
            raise ValidationError("User is banned")
        return phone_number

class PhoneNumberValidationSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate_phone_number(self, phone_number):
        matching_registration_requests = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number).order_by('-code_time')
        if not matching_registration_requests:
            raise ValidationError("Incorrect code")
        
        matching_registration_request = matching_registration_requests[0]
        current_time = datetime.now().timestamp()

        time_since_registration_request = current_time - matching_registration_request.code_time
        request_expired = time_since_registration_request > self.EXPIRATION_TIME
        if request_expired:
            raise ValidationError("Code has expired")
        
        return phone_number
        
    def validate(self, data):
        phone_number = data.get('phone_number')
        code = data.get('code')
        registration_request = PhoneNumberAuthentication.objects.get(phone_number=phone_number)
        if registration_request.code != code:
            raise ValidationError({"code": "Code does not match"})
        return data

# email code
class ResetEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        matching_emails = User.objects.filter(email__iexact=email)
        if not matching_emails:
            raise ValidationError("Email does not exist")
        matching_user = matching_emails[0]
        if matching_user.is_banned:
            raise ValidationError("User is banned")
        return email

class ResetEmailValidationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        email = data.get('email').lower()
        code = data.get('code')
        reset_request = PhoneNumberReset.objects.get(email__iexact=email)
        if reset_request.email_code != code:
            raise ValidationError({"code": "Code does not match"})
        return data

    def validate_email(self, email):
        matching_emails = PhoneNumberReset.objects.filter(
            email__iexact=email).order_by('-email_code_time')
        if not matching_emails:
            raise ValidationError("No reset request")
        
        matching_email = matching_emails[0]

        current_time = datetime.now().timestamp()
        time_since_reset_request = current_time - matching_email.email_code_time
        request_expired = time_since_reset_request > self.EXPIRATION_TIME

        if request_expired:
            raise ValidationError("Reset request expired")
        
        return email

class ResetTextRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = PhoneNumberField()
    token = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        email = data.get('email').lower()
        reset_token = data.get('token')

        matching_reset_requests = PhoneNumberReset.objects.filter(
            email__iexact=email,
            reset_token=reset_token,
        )
        if not matching_reset_requests:
            raise ValidationError({"token": "Invalid reset token"})
        
        return data

    def validate_email(self, email):
        matching_emails = PhoneNumberReset.objects.filter(
            email__iexact=email).order_by('-email_code_time')
        if not matching_emails:
            raise ValidationError("Email did not request reset")
        
        matching_email = matching_emails[0]
        if not matching_email.email_validated:
            raise ValidationError("Email was not validated")

        current_time = datetime.now().timestamp()
        time_since_validation = current_time - matching_email.email_validation_time
        validation_expired = time_since_validation > self.EXPIRATION_TIME

        if validation_expired:
            raise ValidationError("Email validation expired")

        return email
    
    def validate_phone_number(self, phone_number):
        matching_users = User.objects.filter(phone_number=phone_number)
        if matching_users:
            raise ValidationError("Phone number is already in use")

        matching_reset_phone_numbers = PhoneNumberReset.objects.filter(
            phone_number=phone_number).order_by('-phone_number_code_time')
        
        if not matching_reset_phone_numbers:
            return phone_number
        
        matching_reset_phone_number = matching_reset_phone_numbers[0]
        last_request_time = matching_reset_phone_number.phone_number_code_time
        time_since_last_request = get_current_time() - last_request_time
        if time_since_last_request < self.EXPIRATION_TIME:
            raise ValidationError("Phone number is being registered")
        
        return phone_number

class ResetTextValidationSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    code = serializers.CharField()
    token = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        phone_number = data.get('phone_number')
        code = data.get('code')
        reset_token = data.get('token')

        matching_reset_requests = PhoneNumberReset.objects.filter(
            phone_number=phone_number,
            reset_token=reset_token,
        )
        if not matching_reset_requests:
            raise ValidationError({"token": "Invalid reset token"})

        reset_request = PhoneNumberReset.objects.get(phone_number=phone_number)
        if reset_request.phone_number_code != code:
            raise ValidationError({"code": "Code does not match"})

        return data

    def validate_phone_number(self, phone_number):
        matching_phone_numbers = PhoneNumberReset.objects.filter(
            phone_number=phone_number).order_by('-phone_number_code_time')
        if not matching_phone_numbers:
            raise ValidationError("No account was reset with the phone number")
        
        matching_phone_number = matching_phone_numbers[0]

        current_time = datetime.now().timestamp()
        time_since_reset_request = current_time - matching_phone_number.phone_number_code_time
        request_expired = time_since_reset_request > self.EXPIRATION_TIME

        if request_expired:
            raise ValidationError("Phone number reset expired")
        
        return phone_number

class MatchingPhoneNumberRequestSerializer(serializers.Serializer):
    phone_numbers = serializers.ListField(
        child = serializers.CharField()
    )