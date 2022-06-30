from locust import HttpUser, task, between
from locustfiles.validators import (
    api_throttled_or_valid_json,
    contains_blocks, 
    contains_comments, 
    contains_conversations, 
    contains_favorites, 
    contains_friend_requests, 
    contains_match_requests, 
    contains_posts, 
    contains_read_only_users, 
    contains_votes, 
)

class AppLaunchUser(HttpUser):
    wait_time = between(1, 2)

    http_throttled = 429
    http_get_success = 200
    http_post_success = 201
    local_auth_token = "df3b32643068fb94041e54bb316957476d265beb"
    auth_header = {'Authorization': f'Token {local_auth_token}'}

    id = 6
    username = "kevinsunreal"
    password = "randomstringofcharacters1234"
    login_data = {'username': username, 'password': password}

    @task
    def login_and_launch(self):
        self.client.post("api-token/", data=self.login_data)

        self.get_users()
        self.get_posts()
        self.get_conversations()
        self.get_votes()
        self.get_blocks()

        self.client.cookies.clear()
    
    def get_users(self):
        self.api_throttled_or_contains_read_only_users("api/users/")
        self.api_throttled_or_contains_read_only_users("api/matches/")
        self.api_throttled_or_contains_read_only_users("api/friendships/")
    
    def get_posts(self):
        self.api_throttled_or_contains_posts("api/posts/")
        self.api_throttled_or_contains_posts("api/matched-posts/")
        self.api_throttled_or_contains_posts("api/featured-posts/")
        self.api_throttled_or_contains_posts("api/friend-posts/")
        self.api_throttled_or_contains_posts("api/submitted-posts/")

    def get_conversations(self):
        self.api_throttled_or_contains_conversations(
            "api/conversations/")

    def get_votes(self):
        self.api_throttled_or_contains_votes(
            f"api/votes/?voter={self.id}")

    def get_blocks(self):
        self.api_throttled_or_contains_votes(
            f"api/blocks/?blocking_user={self.id}")
        self.api_throttled_or_contains_votes(
            f"api/blocks/?blocked_user={self.id}")

    def get_favorites(self):
        self.api_throttled_or_contains_favorites(
            f"api/favorites/?favoriting_user={self.id}")

    def get_match_requests(self):
        self.api_throttled_or_contains_match_requests(
            f"api/match-requests/?match_requesting_user={self.id}")
        self.api_throttled_or_contains_match_requests(
            f"api/match-requests/?match_requested_user={self.id}")

    def get_friend_requests(self):
        self.api_throttled_or_contains_friend_requests(
            f"api/friend-requests/?friend_requesting_user={self.id}")
        self.api_throttled_or_contains_friend_requests(
            f"api/friend-requests/?friend_requested_user={self.id}")

    def api_throttled_or_contains_friend_requests(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_friend_requests)

    def api_throttled_or_contains_match_requests(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_match_requests)

    def api_throttled_or_contains_favorites(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_favorites)

    def api_throttled_or_contains_blocks(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_blocks)

    def api_throttled_or_contains_votes(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_votes)

    def api_throttled_or_contains_comments(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_comments)

    def api_throttled_or_contains_read_only_users(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_read_only_users)
    
    def api_throttled_or_contains_posts(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_posts)
    
    def api_throttled_or_contains_conversations(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header, 
            contains_conversations)
    
    