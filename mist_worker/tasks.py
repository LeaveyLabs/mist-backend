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
    from mist.models import Post, Mistbox, MistboxPost
    from users.models import User

    for user in User.objects.all():
        if not user.keywords: continue
        
        postset = Post.objects.none()
        for keyword in user.keywords:
            word_in_title = Post.objects.filter(title__icontains=keyword)
            word_in_body = Post.objects.filter(body__icontains=keyword)
            postset = (word_in_title | word_in_body | postset)
            postset = postset.exclude(author=user)
        postset = postset.distinct()

        Mistbox.objects.filter(user=user).delete()
        mistbox = Mistbox.objects.create(user=user)

        for post in postset:
            MistboxPost.objects.create(
                mistbox=mistbox,
                post=post)