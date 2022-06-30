from locust import HttpUser, task, between, TaskSet
from locustfiles.validators import api_throttled_or_valid_json, contains_posts, contains_words


class Search(TaskSet):
    local_auth_token = "df3b32643068fb94041e54bb316957476d265beb"
    auth_header = {'Authorization': f'Token {local_auth_token}'}

    id = 6
    username = "kevinsunreal"
    password = "randomstringofcharacters1234"
    login_data = {'username': username, 'password': password}

    words = ['this', 'is', 'a', 'locust', 'test']

    @task 
    def search_words(self):
        for word in self.words:
            self.api_throttled_or_contains_words(f'api/words/?text={word}')
        
    @task
    def search_posts(self):
        endpoint = 'api/posts/?'
        for word in self.words:
            if word != self.words[-1]:
                endpoint += f"words={word}&"
            else:
                endpoint += f"words={word}"

        self.api_throttled_or_contains_posts(endpoint)

    def api_throttled_or_contains_words(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header,
            contains_words,
        )

    def api_throttled_or_contains_posts(self, endpoint):
        return api_throttled_or_valid_json(
            self.client, 
            endpoint, 
            self.auth_header,
            contains_posts,
        )

class SearchingUser(HttpUser):
    tasks = [Search]
    wait_time = between(1, 2)