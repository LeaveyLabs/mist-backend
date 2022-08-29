import random


def gen_phone():
    second = str(random.randint(1,888)).zfill(3)

    last = (str(random.randint(1,9998)).zfill(4))
    while last in ['1111','2222','3333','4444','5555','6666','7777','8888']:
        last = (str(random.randint(1,9998)).zfill(4))
        
    return f'+1310{second}{last}'

def create_dummy_user_and_token_given_id(id):
    from datetime import date
    from users.models import User
    from rest_framework.authtoken.models import Token

    username_handle = f'testuser{id}'

    user = User.objects.create(
        email=f'{username_handle}@usc.edu',
        username=username_handle,
        date_of_birth=date(2000, 1, 1),
        phone_number=gen_phone(),
    )

    token = Token.objects.create(user=user)

    return (user, token)

