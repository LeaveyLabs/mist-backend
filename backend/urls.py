"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from mist.accessory_views import FavoritedPostsView, FeaturedPostsView, FriendPostsView, FriendshipView, MatchView, MatchedPostsView, SubmittedPostsView
from mist.model_views import BlockView, FavoriteView, FeatureView, FlagView, FriendRequestView, MatchRequestView, PostView, CommentView, MessageView, TagView, VoteView, WordView
from users.views import FinalizePasswordResetView, RegisterUserEmailView, RequestPasswordResetView, ValidatePasswordResetView, ValidateUserEmailView, UserView, ValidateUsernameView

# Models
router = routers.DefaultRouter()
router.register(r'users', UserView, 'user')
router.register(r'posts', PostView, 'post')
router.register(r'comments', CommentView, 'comment')
router.register(r'messages', MessageView, 'message')
router.register(r'votes', VoteView, 'vote')
router.register(r'flags', FlagView, 'flag')
router.register(r'tags', TagView, 'tag')
router.register(r'blocks', BlockView, 'block')
router.register(r'favorites', FavoriteView, 'favorite')
router.register(r'match-requests', MatchRequestView, 'match_request')
router.register(r'friend-requests', FriendRequestView, 'friend_request')

urlpatterns = [
    # Authentication
    path('admin/', admin.site.urls),
    path('api-register-email/', RegisterUserEmailView.as_view()),
    path('api-validate-email/', ValidateUserEmailView.as_view()),
    path('api-validate-username/', ValidateUsernameView.as_view()),
    path('api-token/', obtain_auth_token),
    path('api-request-reset-password/', RequestPasswordResetView.as_view()),
    path('api-validate-reset-password/', ValidatePasswordResetView.as_view()),
    path('api-finalize-reset-password/', FinalizePasswordResetView.as_view()),
    # Database
    path('api/', include(router.urls)),
    path('api/words/', WordView.as_view()),
    path('api/features/', FeatureView.as_view()),
    path('api/matches/', MatchView.as_view()),
    path('api/friendships/', FriendshipView.as_view()),
    path('api/matched-posts/', MatchedPostsView.as_view()),
    path('api/featured-posts/', FeaturedPostsView.as_view()),
    path('api/friend-posts/', FriendPostsView.as_view()),
    path('api/favorited-posts/', FavoritedPostsView.as_view()),
    path('api/submitted-posts/', SubmittedPostsView.as_view()),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)