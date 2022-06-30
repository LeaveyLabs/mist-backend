from locustfiles.launch import AppLaunchUser
from locustfiles.message import MessagingUser
from locustfiles.search import SearchingUser
from locustfiles.register import RegisteringUser
from locustfiles.profile import UpdatingProfileUser
from locustfiles.post import PostingUser 
# from locustfiles.request import RequestingUser
# ^ this one is not quite set up yet 
# because we need to find a way to generate 
# profiles without email for tests