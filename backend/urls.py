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
from mist import views

router = routers.DefaultRouter()
router.register(r'profiles', views.ProfileView, 'profile')
router.register(r'posts', views.PostView, 'post')
router.register(r'comments', views.CommentView, 'comment')
router.register(r'messages', views.MessageView, 'message')
router.register(r'votes', views.VoteView, 'vote')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/words/', views.WordView.as_view()),
    path('api-register/', views.RegisterView.as_view()),
    path('api-validate/', views.ValidateView.as_view()),
    path('api-create-user/', views.CreateUserView.as_view()),
    path('api-token/', obtain_auth_token),
    # TODO: implement OAuth 2.0 login
    # path('accounts/', include('allauth.urls')),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    # path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    # path('dj-rest-auth/account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)