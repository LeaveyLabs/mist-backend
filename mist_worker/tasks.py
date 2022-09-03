import os
import uuid
import requests
from celery import shared_task

@shared_task(name="send_mistbox_notifications_task")
def send_mistbox_notifications_task():
    send_mistbox_notifications()

def send_mistbox_notifications():
    from push_notifications.models import APNSDevice
    APNSDevice.objects.all().send_message(
        "Your mistbox is ready! See who wrote about you today 👀")

@shared_task(name="make_daily_mistboxes_task")
def make_daily_mistboxes_task():
    make_daily_mistboxes()

def make_daily_mistboxes():
    from mist.models import Post, Mistbox
    from users.models import User
    from datetime import datetime, timedelta

    for user in User.objects.all():
        if not user.keywords: continue
        
        twenty_four_hours = timedelta(days=1).total_seconds()
        mistbox_creation_time = datetime.now().timestamp()
        yesterday_creation_time = mistbox_creation_time-twenty_four_hours

        postset = Post.objects.none()
        for keyword in user.keywords:
            word_in_title = Post.objects.filter(
                title__icontains=keyword,
                time_created__gt=yesterday_creation_time)
            word_in_body = Post.objects.filter(
                body__icontains=keyword,
                time_created__gt=yesterday_creation_time)
            postset = (word_in_title | word_in_body | postset)
            postset = postset.exclude(author=user)
        postset = postset.distinct()

        mistbox = Mistbox.objects.create(user=user)

        for post in postset:
            post.mistboxes.add(mistbox)
            post.save()

@shared_task(name="tally_random_upvotes_task")
def tally_random_upvotes_task():
    tally_random_upvotes()

def tally_random_upvotes():
    import datetime
    from random import randint, choice

    from mist.models import Post, PostVote
    from users.models import User

    NUMBER_OF_TEST_VOTERS = 30

    initial_test_voters = User.objects.filter(
        username__icontains='test_voter',
        is_hidden=True)
    
    remaining_test_voters = [
        User(
            username=f'test_voter-{uuid.uuid4()}',
            date_of_birth=datetime.date(2000, 1, 1),
            is_hidden=True,
        )
        for _ in range(NUMBER_OF_TEST_VOTERS - initial_test_voters.count())
    ]
    User.objects.bulk_create(remaining_test_voters)
    
    final_test_voters = User.objects.filter(
        username__icontains='test_voter',
        is_hidden=True).prefetch_related('postvotes')
    
    posts = Post.objects.all()
    emojis = ["🥳", "😂", "🥰", "😍", "🧐", "😭", "❤️", 
    "😰", "👀", "👏", "💘", "😮", "🙄", "😇", "😳", "😶", 
    "🤠", "😦", "🍿", "🔥", "🙂", "🤣"]

    for test_voter in final_test_voters:
        voted_postvote_ids = [
            postvote.id for postvote in test_voter.postvotes.all()
        ]
        unvoted_posts = posts.exclude(id__in=voted_postvote_ids)
        random_unvoted_post = choice(unvoted_posts)
        random_emoji = choice(emojis)
        try:
            PostVote.objects.create(
                post=random_unvoted_post,
                voter=test_voter,
                emoji=random_emoji,
            )
        except:
            continue

@shared_task(name="verify_profile_picture_task")
def verify_profile_picture_task(user_instance):
    verify_profile_picture(user_instance)

def verify_profile_picture(user_instance):
    VERIFIFCATION_SERVER = os.environ.get('VERIFIFCATION_SERVER')
    verification_request = requests.post(
        f'{VERIFIFCATION_SERVER}api-verify-profile-picture/', 
        files={
            'picture': user_instance.picture,
            'confirm_picture': user_instance.confirm_picture,
        },
    )
    user_instance.is_verified = (verification_request.status_code == 200)
    user_instance.is_pending_verification = False
    user_instance.save()