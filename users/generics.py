from rest_framework.authtoken.models import Token

def get_user_from_request(request):
    if not request or not request.auth: return None
    matching_tokens = Token.objects.filter(key=request.auth)
    if not matching_tokens: return None
    matching_token = matching_tokens[0]
    return matching_token.user