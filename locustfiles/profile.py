from locust import HttpUser, task, between, TaskSet
from locustfiles.validators import HttpMethods, api_throttled_or_valid_json, is_anything, is_read_only_user, random_string

class UpdateUsernamePasswordPicture(TaskSet):
    local_auth_token = "df3b32643068fb94041e54bb316957476d265beb"
    auth_header = {'Authorization': f'Token {local_auth_token}'}

    id = 6
    username = "kevinsunreal"
    password = "randomstringofcharacters1234"

    @task
    def update_username(self):
        username_data = {
            "username": self.username,
        }
        self.api_throttled_or_valid_user(
            endpoint=f'api/users/{self.id}/', 
            data=username_data,
        )

    @task
    def update_password(self):
        password_data = {
            "password": self.password,
        }
        self.api_throttled_or_valid_user(
            endpoint=f'api/users/{self.id}/', 
            data=password_data,
        )

    @task
    def update_picture(self):
        files = {'media': open('../test_assets/test.jpeg', 'rb')}
        self.api_throttled_or_valid_user(
            endpoint=f'api/users/{self.id}/',
            data=None,
            files=files,
        )

    def api_throttled_or_valid_user(self, endpoint, data, files=None):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint=endpoint,
            headers=self.auth_header,
            validator=is_read_only_user,
            data=data,
            method=HttpMethods.PATCH,
            files=files,
        )

class UpdatingProfileUser(HttpUser):
    tasks = [UpdateUsernamePasswordPicture]
    wait_time = between(1, 2)