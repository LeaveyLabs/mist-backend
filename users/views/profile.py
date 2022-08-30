from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from users.generics import get_user_from_request

from users.serializers import ProfilePictureVerificationSerializer

class VerifyProfilePicture(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        verification = ProfilePictureVerificationSerializer(data=request.data)
        verification.is_valid(raise_exception=True)

        user = get_user_from_request(request)
        user.picture = request.data.get('picture')
        user.is_validated = True
        user.save()

        return Response(
            {
                "status": "success",
            }, 
            status=status.HTTP_200_OK)