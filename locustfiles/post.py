import json
import random
from locust import HttpUser, task, between, TaskSet
from locustfiles.validators import HttpMethods, api_throttled_or_valid_json, is_anything, is_comment, is_favorite, is_post, is_vote, random_string

class AllPostInteractions(TaskSet):
    local_auth_token = "df3b32643068fb94041e54bb316957476d265beb"
    auth_header = {'Authorization': f'Token {local_auth_token}', "Content-Type": "application/json"}

    id = 6
    username = "kevinsunreal"
    password = "randomstringofcharacters1234"

    post_id_queue = []
    post_id_to_comment_ids = {}

    voted_posts = []
    favorited_posts = []

    number_of_posts = 10

    def on_start(self):
        for _ in range(self.number_of_posts):
            self.post()
    
    def on_quite(self):
        for _ in range(self.number_of_posts):
            self.delete_post()

    @task
    def run_all_post_interactions(self):
        self.vote()
        self.unvote()

        self.favorite()
        self.unfavorite()
        
        self.comment()
        self.delete_comment()
    
    def post(self):
        post_obj = {
            'title': 'This is a Locust Test',
            'body': 'This is a Locust Test',
            'author': self.id,
        }
        post_json = json.dumps(post_obj)
        response_post = self.api_throttled_or_valid_post(
            'api/posts/', data=post_json, method=HttpMethods.POST)
        if response_post:
            self.post_id_queue.append(response_post['id'])

    def delete_post(self):
        if not self.post_id_queue: return
        post_id = self.post_id_queue.pop()
        self.api_throttled_or_valid_status_code(
            f'api/posts/{post_id}/', method=HttpMethods.DELETE)
        if post_id in self.voted_posts:
            self.voted_posts.remove(post_id)
        if post_id in self.favorited_posts:
            self.favorited_posts.remove(post_id)
        if post_id in self.post_id_to_comment_ids:
            self.post_id_to_comment_ids.pop(post_id)

    def vote(self):
        remaining_posts = [
            post_id for post_id in self.post_id_queue 
            if post_id not in self.voted_posts]
        if not remaining_posts: return
        post_id = random.choice(remaining_posts)
        vote_obj = {
            'post': post_id,
            'voter': self.id,
        }
        vote_json = json.dumps(vote_obj)
        response_vote = self.api_throttled_or_valid_vote(
            'api/votes/', data=vote_json, method=HttpMethods.POST)
        if response_vote:
            self.voted_posts.append(post_id)

    def unvote(self):
        if not self.voted_posts: return
        voted_post = self.voted_posts.pop()
        response_vote = self.api_throttled_or_valid_status_code(
            f'api/delete-vote/?voter={self.id}&post={voted_post}',
            method=HttpMethods.DELETE)
        if not response_vote:
            self.voted_posts.append(voted_post)

    def favorite(self):
        remaining_posts = [
            post_id for post_id in self.post_id_queue 
            if post_id not in self.favorited_posts]
        if not remaining_posts: return
        post_id = random.choice(remaining_posts)
        favorite_obj = {
            'post': post_id,
            'favoriting_user': self.id,
        }
        favorite_json = json.dumps(favorite_obj)
        response_favorite = self.api_throttled_or_valid_favorite(
            'api/favorites/', data=favorite_json, method=HttpMethods.POST)
        if response_favorite:
            self.favorited_posts.append(post_id)

    def unfavorite(self):
        if not self.favorited_posts: return
        favorited_post = self.favorited_posts.pop()
        response_favorite = self.api_throttled_or_valid_status_code(
            f'api/delete-favorite/?favoriting_user={self.id}&post={favorited_post}',
            method=HttpMethods.DELETE
        )
        if not response_favorite:
            self.favorited_posts.append(favorited_post)

    def comment(self):
        remaining_posts = [
            post_id for post_id in self.post_id_queue 
            if post_id not in self.voted_posts]
        if not remaining_posts: return
        post_id = random.choice(remaining_posts)
        comment_obj = {
            'body': random_string(),
            'post': post_id,
            'author': self.id,
        }
        comment_json = json.dumps(comment_obj)
        response_comment = self.api_throttled_or_valid_comment(
            'api/comments/', 
            data=comment_json, 
            method=HttpMethods.POST)
        if not response_comment: return
        if post_id not in self.post_id_to_comment_ids:
            self.post_id_to_comment_ids[post_id] = []
        self.post_id_to_comment_ids[post_id].append(response_comment['id'])

    def delete_comment(self):
        if not self.post_id_to_comment_ids: return
        post_id = random.choice(list(self.post_id_to_comment_ids.keys()))
        if not post_id in self.post_id_to_comment_ids: return
        if not self.post_id_to_comment_ids[post_id]: return
        comment_id = self.post_id_to_comment_ids[post_id].pop()
        self.api_throttled_or_valid_status_code(
            f'api/comments/{comment_id}/',
            method=HttpMethods.DELETE
        )
        if not self.post_id_to_comment_ids[post_id]:
            self.post_id_to_comment_ids.pop(post_id)

    def api_throttled_or_valid_status_code(self, endpoint, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            headers=self.auth_header,
            validator=is_anything,
            method=method,
        )

    def api_throttled_or_valid_post(self, endpoint, data, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            data=data,
            headers=self.auth_header,
            validator=is_post,
            method=method,
        )
    
    def api_throttled_or_valid_vote(self, endpoint, data, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            data=data,
            headers=self.auth_header,
            validator=is_vote,
            method=method,
        )

    def api_throttled_or_valid_comment(self, endpoint, data, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            data=data,
            headers=self.auth_header,
            validator=is_comment,
            method=method,
        )

    def api_throttled_or_valid_favorite(self, endpoint, data, method):
        return api_throttled_or_valid_json(
            self.client,
            endpoint=endpoint,
            data=data,
            headers=self.auth_header,
            validator=is_favorite,
            method=method,
        )

class PostingUser(HttpUser):
    tasks = [AllPostInteractions]
    wait_time = between(1, 2)