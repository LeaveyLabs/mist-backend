import os
import uuid
import requests
from celery import shared_task

from mist.models import NotificationTypes

@shared_task(name="send_mistbox_notifications_task")
def send_mistbox_notifications_task():
    send_mistbox_notifications()

def send_mistbox_notifications():
    from push_notifications.models import APNSDevice
    APNSDevice.objects.all().send_message(
        "your mistbox opens have refreshed! pick out 5 new mists containing your keywords 💌",
        extra={
            "type": NotificationTypes.DAILY_MISTBOX,
        })

@shared_task(name="schedule_make_your_day_mist_notifications_task")
def schedule_make_your_day_mist_notifications_task():
    import random
    from backend import celery_app
    t = random.randint(3600*1, 3600*8)
    celery_app.send_task(name="send_make_your_day_mist_notifications_task", countdown=t)

@shared_task(name="send_make_your_day_mist_notifications_task")
def send_make_your_day_mist_notifications_task():
    send_make_your_day_mist_notifications()

def send_make_your_day_mist_notifications():
    from push_notifications.models import APNSDevice
    APNSDevice.objects.all().send_message(
        "did anyone make your day today? make theirs back with a mist 💞",
        extra={
            "type": NotificationTypes.MAKE_SOMEONES_DAY,
        })

@shared_task(name="reset_mistbox_opens_task")
def reset_mistbox_opens_task():
    reset_mistbox_opens()

def reset_mistbox_opens():
    from mist.models import Mistbox
    for mistbox in Mistbox.objects.all():
        mistbox.opens_used_today = 0
        mistbox.save()

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

    emojis += ["❤️", "❤️", "❤️", "❤️", "❤️", "❤️", "❤️", "❤️"]
    emojis += ["😍", "😍", "😍"]
    emojis += ["👀", "👀"]
    emojis += ["🔥"]

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
def verify_profile_picture_task(user_id):
    verify_profile_picture(user_id)

def verify_profile_picture(user_id):
    from users.models import User

    VERIFICATION_SERVER = os.environ.get('VERIFICATION_SERVER')
    
    matching_users = User.objects.filter(id=user_id)
    if not matching_users.exists(): return False
    
    matching_user = matching_users[0]
    
    verification_request = requests.post(
        f'{VERIFICATION_SERVER}api-verify-profile-picture/', 
        files={
            'picture': matching_user.picture,
            'confirm_picture': matching_user.confirm_picture,
        },
    )
    matching_user.is_verified = (verification_request.status_code == 200)
    matching_user.is_pending_verification = False
    matching_user.save()
    
    return True