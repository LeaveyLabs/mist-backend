import json
import random
from locust import HttpUser, task, between, TaskSet
from locustfiles.validators import HttpMethods, User, api_throttled_or_valid_json, is_anything, is_friend_request, is_match_request, random_string

class AllRequestInteractions(TaskSet):
    user_1 = User(1, "eb622f9ac993c621391de3418bc18f19cb563a61")
    user_2 = User(6, "df3b32643068fb94041e54bb316957476d265beb")
    users = [user_1, user_2]

    sender = None
    receiver = None
    auth_header = None   

    @task
    def all_request_interactions(self):
        self.select_users()
        self.friend()
        self.match()
        self.unfriend()
        self.unmatch()

    def select_users(self):
        self.sender = random.choice(self.users)
        self.receiver = random.choice(
            [user for user in self.users 
            if user != self.user])
        self.auth_header = {
            'Authorization': f'Token {self.sender.token}',  
            "Content-Type": "application/json"}
        
    def friend(self):
        friend_data = json.dumps(
            {
                'friend_requesting_user': self.sender.id,
                'friend_requested_user': self.receiver.id,
            }
        )
        self.api_throttled_or_valid_friend_request(
            endpoint=f'api/friend-requests/',
            data=friend_data,
            method=HttpMethods.POST,
        )
    
    def unfriend(self):
        self.api_throttled_or_valid_friend_request(
            endpoint=f'api/delete-friend-request/?friend_requesting_user={self.sender.id}&friend_requested_user={self.receiver.id}',
            method=HttpMethods.DELETE,
        )

    def match(self):
        match_data = json.dumps(
            {
                'match_requesting_user': self.sender.id,
                'match_requested_user': self.receiver.id,
                'post': 1,
            }
        )
        self.api_throttled_or_valid_match_request(
            endpoint=f'api/match-requests/',
            data=match_data,
            method=HttpMethods.POST,
        )
    
    def unmatch(self):
        self.api_throttled_or_valid_friend_request(
            endpoint=f'api/delete-match-request/?match_requesting_user={self.sender.id}&match_requested_user={self.receiver.id}',
            method=HttpMethods.DELETE,
        )

    def api_throttled_or_valid_status_code(self, endpoint, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            headers=self.auth_header,
            validator=is_anything,
            method=method,
        )

    def api_throttled_or_valid_friend_request(self, endpoint, method, data=None):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            data=data,
            headers=self.auth_header,
            validator=is_friend_request,
            method=method,
        )

    def api_throttled_or_valid_match_request(self, endpoint, data, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            data=data,
            headers=self.auth_header,
            validator=is_match_request,
            method=method,
        )


class RequestingUser(HttpUser):
    tasks = [AllRequestInteractions]
    wait_time = between(1, 2)