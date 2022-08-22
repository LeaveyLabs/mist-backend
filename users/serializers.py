from datetime import date, datetime, timedelta
import re
from django.forms import ValidationError
from rest_framework import serializers

from users.generics import get_current_time
from .models import PasswordReset, PhoneNumberAuthentication, PhoneNumberReset, User, EmailAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from phonenumber_field.serializerfields import PhoneNumberField

class ReadOnlyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'picture', )
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'picture', )

class CompleteUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, write_only=True)
    confirm_picture = serializers.ImageField(write_only=True)

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()
    MEGABYTE_LIMIT = 10

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password',
        'first_name', 'last_name', 'picture', 'confirm_picture',
        'phone_number', 'date_of_birth', 'sex', 'latitude', 
        'longitude', 'keywords')
    
    def email_matches_name(email, first_name, last_name):
        first_name_in_email = email.find(first_name) != -1
        last_name_in_email = email.find(last_name) != -1
        return first_name_in_email or last_name_in_email

    def picture_below_size_limit(self, picture, field_name):
        filesize = picture.size
        if filesize > self.MEGABYTE_LIMIT * 1024 * 1024:
            raise ValidationError({f"{field_name}": f"Max file size is {self.MEGABYTE_LIMIT}MB"})
        return picture

    def is_match(self, picture, confirm_picture):
        return True
        # processed_picture = face_recognition.load_image_file(picture)
        # processed_confirm = face_recognition.load_image_file(confirm_picture)
        # picture_encodings = face_recognition.face_encodings(processed_picture)
        # confirm_encodings = face_recognition.face_encodings(processed_confirm)
        # results = face_recognition.compare_faces(picture_encodings, confirm_encodings[0])
        # return results[0]

    def validate(self, data):
        picture = data.get('picture')
        confirm_picture = data.get('confirm_picture')
        if not picture and not confirm_picture: return data
        if picture and not confirm_picture: 
            raise ValidationError(
                {
                    "picture": "Picture must be validated, input confirm_picture",
                }
            )
        if not self.is_match(picture, confirm_picture):
            raise ValidationError(
                {
                    "picture": "Does not contain the same person as confirm_picture",
                    "confirm_picture": "Does not contain the same person as picture"
                }
            )
        return data

    def validate_username(self, username):
        alphanumeric_dash_and_underscores_only = "^[A-Za-z0-9_-]*$"
        if not re.match(alphanumeric_dash_and_underscores_only, username):
            raise ValidationError({"username": "Username must contain only letters, numbers, underscores, or hypens."})
        return username
    
    def validate_date_of_birth(self, date_of_birth):
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        if age < 18:
            raise ValidationError({"date_of_birth": "Users must be over 18 years old."})
        return date_of_birth
    
    def validate_email(self, email):
        users_with_matching_email = User.objects.filter(email__iexact=email)
        if users_with_matching_email:
            raise ValidationError({"email": "Email has already been registered."})
        return email
    
    def validate_password(self, password):
        validate_password(password)
        return password
    
    def validate_picture(self, picture):
        return self.picture_below_size_limit(picture, 'picture')
    
    def validate_confirm_picture(self, confirm_picture):
        return self.picture_below_size_limit(confirm_picture, 'confirm_picture')
    
    def validate_keywords(self, keywords):
        return [keyword.lower() for keyword in keywords]

    def verify_email_authentication(self, validated_data):
        email = validated_data.get('email').lower()
        validations_with_matching_email = EmailAuthentication.objects.filter(
            email__iexact=email)
        email_auth_requests = validations_with_matching_email.order_by('-validation_time')

        if not email_auth_requests:
            raise serializers.ValidationError({"email": "Email was not registered."})

        most_recent_auth_request = email_auth_requests[0]

        if not most_recent_auth_request.validated:
            raise serializers.ValidationError({"email": "Email was not validated."})

        current_time = datetime.now().timestamp()
        time_since_validation = current_time - most_recent_auth_request.validation_time
        validation_expired = time_since_validation > self.EXPIRATION_TIME

        if validation_expired:
            raise serializers.ValidationError({"email": "Email validation expired."})

        users_with_matching_email = User.objects.filter(email__iexact=email)
        if len(users_with_matching_email):
            raise serializers.ValidationError({"email": "Email already taken."})
    
    def verify_phone_number(self, validated_data):
        email = validated_data.get('email').lower()
        phone_number = validated_data.get('phone_number').lower()
        matching_validations = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number,
            email__iexact=email).order_by('-validation_time')

        if not matching_validations:
            raise serializers.ValidationError({"phone_number": "Phone number was not registered."})

        most_recent_auth_request = matching_validations[0]

        if not most_recent_auth_request.validated:
            raise serializers.ValidationError({"phone_number": "Phone number was not validated."})

        current_time = datetime.now().timestamp()
        time_since_validation = current_time - most_recent_auth_request.validation_time
        validation_expired = time_since_validation > self.EXPIRATION_TIME

        if validation_expired:
            raise serializers.ValidationError({"phone_number": "Phone number validation expired."})

        users_with_matching_phone_number = User.objects.filter(phone_number=phone_number)
        if len(users_with_matching_phone_number):
            raise serializers.ValidationError({"phone_number": "Phone number already taken."})

    def hash_password(self, validated_data):
        raw_password = validated_data.get('password')
        hashed_password = make_password(raw_password)
        validated_data.update({'password': hashed_password})

    def verify_username(self, validated_data):
        username = validated_data.get('username').lower()

        if not username:
            raise ValidationError({"username": "Username was not provided."})

        alphanumeric_dash_period_and_underscores_only = "^[A-Za-z0-9_\.]*$"
        if not re.match(alphanumeric_dash_period_and_underscores_only, username):
            raise ValidationError({"username": "Username must contain only letters, numbers, underscores, or periods."})

        users_with_matching_username = User.objects.filter(username__iexact=username)
        if users_with_matching_username:
            raise ValidationError({"username": "Username is not unique."})

    def create(self, validated_data):
        self.verify_email_authentication(validated_data)
        # self.verify_phone_number(validated_data)
        self.verify_username(validated_data)
        self.hash_password(validated_data)
        validated_data.pop('confirm_picture')
        return User.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        instance.email = validated_data.get('email', instance.email).lower()
        instance.username = validated_data.get('username', instance.username).lower()
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.picture = validated_data.get('picture', instance.picture)
        instance.latitude = validated_data.get('latitude', instance.latitude)
        instance.longitude = validated_data.get('longitude', instance.longitude)
        instance.keywords = validated_data.get('keywords', instance.keywords)
        instance.save()
        return instance
    
    def partial_update(self, instance, validated_data):
        return self.update(self, instance, validated_data)

class LoginSerializer(serializers.Serializer):
    email_or_username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        email_or_username = data.get('email_or_username').lower()
        password = data.get('password')

        users_with_matching_email = User.objects.filter(email__iexact=email_or_username)
        if users_with_matching_email:
            user_with_matching_email = users_with_matching_email[0]
            email_or_username = user_with_matching_email.username
            
        user = authenticate(username=email_or_username, password=password)
        if user:
            if not user.is_active:
                raise serializers.ValidationError({
                    "non_field_errors": [
                        "User account is disabled."
                    ]
                })
        else:
            raise serializers.ValidationError({
                    "non_field_errors": [
                        "Unable to log in with provided credentials."
                    ]
                })

        data['user'] = user
        return data
            
            

class UserEmailRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    # ACCEPTABLE_DOMAINS = ('usc.edu', 'gmail.com', 'protonmail.com', 'yahoo.com', 'icloud.com')
    
    def validate_email(self, email):
        lowercased_email = email.lower()

        users_with_matching_email = User.objects.filter(email__iexact=lowercased_email)
        
        if users_with_matching_email:
            raise ValidationError({"email": "Email has already been registered."})

        # domain = email.split('@')[1]
        # if domain not in self.ACCEPTABLE_DOMAINS:
        #     raise ValidationError({"email": "Email has an invalid domain."})

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
            raise ValidationError({"email": "Email was not registered."})

        code = data.get('code')
        registration = registrations_with_matching_email[0]
        if code != registration.code:
            raise ValidationError({"code": "Code does not match."})

        current_time = datetime.now().timestamp()
        time_since_registration = current_time - registration.code_time 
        registration_expired = time_since_registration > self.EXPIRATION_TIME

        if registration_expired:
            raise ValidationError({"code": "Code expired (10 minutes)."})

        return data

class UsernameValidationRequestSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, data):
        username = data.get('username').lower()

        if not username:
            raise ValidationError({"username": "Username was not provided."})

        alphanumeric_dash_period_and_underscores_only = "^[A-Za-z0-9_\.]*$"
        if not re.match(alphanumeric_dash_period_and_underscores_only, username):
            raise ValidationError({"username": "Username must contain only letters, numbers, underscores, or periods."})

        users_with_matching_username = User.objects.filter(username__iexact=username)
        if users_with_matching_username:
            raise ValidationError({"username": "Username is not unique."})

        return data

class PasswordValidationRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username').lower()
        password = data.get('password')

        user = User(username=username)
        validate_password(password=password, user=user)

        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        if not User.objects.filter(email__iexact=email):
            raise ValidationError({"email": "Email does not exist."})
        return email

class PasswordResetValidationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate_email(self, email):
        matching_password_reset_requests = PasswordReset.objects.filter(email__iexact=email)
        if not matching_password_reset_requests:
            raise ValidationError({"email": "Email did not request a password reset."})

        password_reset_request = matching_password_reset_requests[0]

        current_time = datetime.now().timestamp()
        time_since_reset_request = current_time - password_reset_request.code_time
        request_expired = time_since_reset_request > self.EXPIRATION_TIME

        if request_expired:
            raise ValidationError({"code": "Code expired."})
        
        return email

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        password_reset_request = PasswordReset.objects.get(email__iexact=email)
        if password_reset_request.code != code:
            raise ValidationError({"code": "Code does not match."})
        return data

class PasswordResetFinalizationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate_email(self, email):
        matching_password_reset_requests = PasswordReset.objects.filter(email__iexact=email)
        if not matching_password_reset_requests:
            raise ValidationError({"email": "Email did not request a password reset."})
        
        password_reset_request = matching_password_reset_requests[0]
        if not password_reset_request.validated:
            raise ValidationError({"email": "Reset request has not been validated."})
        
        current_time = datetime.now().timestamp()
        time_since_reset_request = current_time - password_reset_request.validation_time
        request_expired = time_since_reset_request > self.EXPIRATION_TIME
        if request_expired:
            raise ValidationError({"email": "Request validation has expired."})
        
        return email

    def validate_password(self, password):
        validate_password(password)
        return password

class PhoneNumberRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = PhoneNumberField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        email = data.get('email').lower()
        phone_number = data.get('phone_number')

        matching_regsitrations = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number,
        ).order_by('-code_time')

        if not matching_regsitrations:
            return data
        
        matching_regsitration = matching_regsitrations[0]

        current_time = datetime.now().timestamp()
        time_since_registration = current_time - matching_regsitration.code_time
        registration_expired = time_since_registration > self.EXPIRATION_TIME

        if not registration_expired and matching_regsitration.email != email:
            raise ValidationError({"phone_number": "Phone number is being registered by someone else."})

        return data

    def validate_email(self, email):
        matching_emails = User.objects.filter(email__iexact=email)
        if matching_emails:
            raise ValidationError({"email": "Email is in use, try the reset phone number API."})
        return email
    
    def validate_phone_number(self, phone_number):
        matching_phone_numbers = User.objects.filter(phone_number=phone_number)
        if matching_phone_numbers:
            raise ValidationError({"phone_number": "Phone number is in use."})
        return phone_number

class LoginCodeRequestSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()

    def validate_phone_number(self, phone_number):
        matching_users = User.objects.filter(phone_number=phone_number)
        if not matching_users:
            raise ValidationError({"phone_number": "User with phone number does not exist."})
        return phone_number

class PhoneNumberValidationSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate_phone_number(self, phone_number):
        matching_registration_requests = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number).order_by('-code_time')
        if not matching_registration_requests:
            raise ValidationError({"phone_number": "No reset request with matching phone number."})
        
        matching_registration_request = matching_registration_requests[0]
        current_time = datetime.now().timestamp()

        time_since_registration_request = current_time - matching_registration_request.code_time
        request_expired = time_since_registration_request > self.EXPIRATION_TIME
        if request_expired:
            raise ValidationError({"phone_number": "Code has expired."})
        
        return phone_number
        
    def validate(self, data):
        phone_number = data.get('phone_number')
        code = data.get('code')
        registration_request = PhoneNumberAuthentication.objects.get(phone_number=phone_number)
        if registration_request.code != code:
            raise ValidationError({"code": "Code does not match."})
        return data

# email code
class ResetEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        matching_emails = User.objects.filter(email__iexact=email)
        if not matching_emails:
            raise ValidationError({"email": "Email does not exist."})
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
            raise ValidationError({"code": "Code does not match."})
        return data

    def validate_email(self, email):
        matching_emails = PhoneNumberReset.objects.filter(
            email__iexact=email).order_by('-email_code_time')
        if not matching_emails:
            raise ValidationError({"email": "Email did not request a phone number reset."})
        
        matching_email = matching_emails[0]

        current_time = datetime.now().timestamp()
        time_since_reset_request = current_time - matching_email.email_code_time
        request_expired = time_since_reset_request > self.EXPIRATION_TIME

        if request_expired:
            raise ValidationError({"email": "Reset request expired."})
        
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
            raise ValidationError({"token": "Invalid reset token."})
        
        return data

    def validate_email(self, email):
        matching_emails = PhoneNumberReset.objects.filter(
            email__iexact=email).order_by('-email_code_time')
        if not matching_emails:
            raise ValidationError({"email": "Email did not request a phone number reset."})
        
        matching_email = matching_emails[0]
        if not matching_email.email_validated:
            raise ValidationError({"email": "Email was not validated."})

        current_time = datetime.now().timestamp()
        time_since_validation = current_time - matching_email.email_validation_time
        validation_expired = time_since_validation > self.EXPIRATION_TIME

        if validation_expired:
            raise ValidationError({"email": "Email validation expired."})

        return email
    
    def validate_phone_number(self, phone_number):
        matching_users = User.objects.filter(phone_number=phone_number)
        if matching_users:
            raise ValidationError({"phone_number": "Phone number is already in use."})

        matching_reset_phone_numbers = PhoneNumberReset.objects.filter(
            phone_number=phone_number).order_by('-phone_number_code_time')
        
        if not matching_reset_phone_numbers:
            return phone_number
        
        matching_reset_phone_number = matching_reset_phone_numbers[0]
        last_request_time = matching_reset_phone_number.phone_number_code_time
        time_since_last_request = get_current_time() - last_request_time
        if time_since_last_request < self.EXPIRATION_TIME:
            raise ValidationError({"phone_number": "Phone number is being registered."})
        
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
            raise ValidationError({"token": "Invalid reset token."})

        reset_request = PhoneNumberReset.objects.get(phone_number=phone_number)
        if reset_request.phone_number_code != code:
            raise ValidationError({"code": "Code does not match."})

        return data

    def validate_phone_number(self, phone_number):
        matching_phone_numbers = PhoneNumberReset.objects.filter(
            phone_number=phone_number).order_by('-phone_number_code_time')
        if not matching_phone_numbers:
            raise ValidationError({"phone_number": "No account was reset with the phone number."})
        
        matching_phone_number = matching_phone_numbers[0]

        current_time = datetime.now().timestamp()
        time_since_reset_request = current_time - matching_phone_number.phone_number_code_time
        request_expired = time_since_reset_request > self.EXPIRATION_TIME

        if request_expired:
            raise ValidationError({"phone_number": "Phone number reset expired."})
        
        return phone_number

class MatchingPhoneNumberRequestSerializer(serializers.Serializer):
    phone_numbers = serializers.ListField(
        child = serializers.CharField()
    )