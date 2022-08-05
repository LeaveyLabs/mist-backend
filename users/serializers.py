from datetime import date, datetime, timedelta
from django.forms import ValidationError
from rest_framework import serializers
from .models import PasswordReset, PhoneNumberAuthentication, User, EmailAuthentication
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
        'date_of_birth', 'sex', 'latitude', 'longitude', )
    
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
    
    def validate_date_of_birth(self, date_of_birth):
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        if age < 18:
            raise ValidationError({"date_of_birth": "Users must be over 18 years old."})
        return date_of_birth
    
    def validate_email(self, email):
        emailValidator = UserEmailRegistrationSerializer(data={"email":email})
        emailValidator.is_valid(raise_exception=True)
        return email
    
    def validate_password(self, password):
        validate_password(password)
        return password
    
    def validate_picture(self, picture):
        return self.picture_below_size_limit(picture, 'picture')
    
    def validate_confirm_picture(self, confirm_picture):
        return self.picture_below_size_limit(confirm_picture, 'confirm_picture')

    def create(self, validated_data):
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

        username = validated_data.get('username').lower()
        users_with_matching_username = User.objects.filter(username__iexact=username)
        
        if len(users_with_matching_username):
            raise serializers.ValidationError({"username": "Username already taken."})
        
        raw_password = validated_data.get('password')
        hashed_password = make_password(raw_password)
        validated_data.update({'password': hashed_password})

        picture = validated_data.get('picture')
        if not picture:
            raise serializers.ValidationError({"picture": "Picture is required."})

        confirm_picture = validated_data.get('confirm_picture')
        if not confirm_picture:
            raise serializers.ValidationError({"confirm_picture": "Picture is required."})
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

        missing_fields = {}
        if not email_or_username:
            missing_fields['email_or_username'] = "Email or username is required."
        if not password:
            missing_fields['password'] = "Password is required."
        if missing_fields: 
            raise serializers.ValidationError(missing_fields)

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
            
            

class UserEmailRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAuthentication
        fields = ('email',)

    # ACCEPTABLE_DOMAINS = ('usc.edu', 'gmail.com', 'protonmail.com', 'yahoo.com', 'icloud.com')
    
    def validate(self, data):
        email = data.get('email').lower()

        users_with_matching_email = User.objects.filter(email__iexact=email)
        if users_with_matching_email:
            raise ValidationError({"email": "Email has already been registered."})

        # domain = email.split('@')[1]
        # if domain not in self.ACCEPTABLE_DOMAINS:
        #     raise ValidationError({"email": "Email has an invalid domain."})

        return data

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

        missing_fields = {}
        if not username:
            missing_fields['username'] = "Username was not provided"
        if not password:
             missing_fields['password'] = "Password was not provided"
        if missing_fields:
            raise ValidationError(missing_fields)

        user = User(username=username)
        validate_password(password=password, user=user)

        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        if not User.objects.filter(email=email):
            raise ValidationError({"email": "Email does not exist."})
        return email

class PasswordResetValidationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate_email(self, email):
        matching_password_reset_requests = PasswordReset.objects.filter(email=email)
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
        password_reset_request = PasswordReset.objects.get(email=email)
        if password_reset_request.code != code:
            raise ValidationError({"code": "Code does not match."})
        return data

class PasswordResetFinalizationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate_email(self, email):
        matching_password_reset_requests = PasswordReset.objects.filter(email=email)
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

    def validate_email(self, email):
        matching_users = User.objects.filter(email__iexact=email.lower())
        if not matching_users:
            raise ValidationError({"email": "User with email does not exist."})
        return email

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

    def validate_phone_number(self, phone_number):
        matching_registration_requests = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number).order_by('-code_time')
        if not matching_registration_requests:
            raise ValidationError({"phone_number": "No registration with matching phone number."})
        
        matching_registration_request = matching_registration_requests[0]
        current_time = datetime.now().timestamp()

        time_since_registration_request = current_time - matching_registration_request.validation_time
        request_expired = time_since_registration_request > self.EXPIRATION_TIME
        if request_expired:
            raise ValidationError({"phone_number": "Request validation has expired."})
        
        return phone_number
        
    def validate(self, data):
        phone_number = data.get('phone_number')
        code = data.get('code')
        registration_request = PhoneNumberAuthentication.objects.get(phone_number=phone_number)
        if registration_request.code != code:
            raise ValidationError({"code": "Code does not match."})
        return data