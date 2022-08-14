import os
from twilio.rest import Client

environment = os.getenv('ENVIRONMENT')

class TwilioTestClient:

    def __init__(self, sid, token):
        self.sid = sid
        self.token = token
        self.messages = TwillioTestClientMessages()

class TwillioTestClientMessages:

    created = []

    def create(self, to, from_, body):
        self.created.append({
            'to': to,
            'from_': from_,
            'body': body
        })

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_phone_number = os.environ['TWILIO_PHONE_NUMBER']

if environment == 'dev':
    twilio_client = TwilioTestClient(account_sid, auth_token)
else:
    twilio_client = Client(account_sid, auth_token)