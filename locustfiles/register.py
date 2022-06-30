from locust import HttpUser, task, between, TaskSet
from locustfiles.validators import HttpMethods, api_throttled_or_valid_json, is_anything, random_string


class RegisterEmailAndCheckUsername(TaskSet):
    @task
    def register_email(self):
        email = f"{random_string()}@usc.edu"
        email_data = {"email": email}
        self.api_throttled_or_valid_status_code("api-register-email/", email_data)
    
    @task
    def check_username(self):
        username = random_string()
        username_data = {"username": username}
        self.api_throttled_or_valid_status_code("api-validate-username/", username_data)

    def api_throttled_or_valid_status_code(self, endpoint, email_data):
        return api_throttled_or_valid_json(
            self.client,
            endpoint,
            data=email_data,
            headers=None,
            validator=is_anything,
            method=HttpMethods.POST,
        )

class RegisteringUser(HttpUser):
    tasks = [RegisterEmailAndCheckUsername]
    wait_time = between(1, 2)