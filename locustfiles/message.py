import os
import json
from locust import HttpUser, task, between, TaskSet
from locustfiles.validators import User, is_success, is_throttled, is_message_response
from websocket import create_connection
import random

class SendThenReceiveMessage(TaskSet):
    user_1 = User(1, "eb622f9ac993c621391de3418bc18f19cb563a61")
    user_2 = User(6, "df3b32643068fb94041e54bb316957476d265beb")
    users = [user_1, user_2]
    sender = None
    receiver = None

    statements = [
        'Hello', 
        'How are you?', 
        'This chat is nice',
    ]
       
    @task
    def send_and_receive(self):
        self.init_chat()
        self.send_message()
        self.receive_message()
        self.disconnect()
        self.client.cookies.clear()

    def init_chat(self):
        uri = os.environ["CHAT_SOCKET"]
        self.ws = create_connection(uri)
        self.sender = random.choice(self.users)
        self.receiver = random.choice([user for user in self.users if user != self.sender])

        init_message = {
            "type": "init",
            "sender": self.sender.id,
            "receiver": self.receiver.id,
        }
        init_message_json = json.dumps(init_message)
        self.ws.send(init_message_json)
        response_obj = json.loads(self.ws.recv())
        if is_throttled(response_obj): return
        assert is_success(response_obj), "Chat initialization failed."

    def send_message(self):
        statement = random.choice(self.statements)
        message = {
            "type": "message",
            "sender": self.sender.id,
            "receiver": self.receiver.id,
            "body": statement,
            "token": self.sender.token,
        }
        message_json = json.dumps(message)
        self.ws.send(message_json)
        response_obj = json.loads(self.ws.recv())
        if is_throttled(response_obj): return
        assert is_message_response(response_obj), "Sent text was not a message."

    def receive_message(self):
        response_obj = json.loads(self.ws.recv())
        if is_throttled(response_obj): return
        assert is_message_response(response_obj), "Received text was not a message."

    def disconnect(self):
        self.ws.close()
        
class MessagingUser(HttpUser):
    tasks = [SendThenReceiveMessage]
    wait_time = between(5, 15)