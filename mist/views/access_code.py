from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from mist.serializers import AccessCodeClaimSerializer, AccessCodeSerializer
from mist.models import AccessCode, Badge
from users.generics import get_user_from_request

class ClaimAccessCodeView(generics.ListCreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = AccessCodeSerializer

    def get_queryset(self):
        code = self.request.query_params.get('code')
        if not code: return AccessCode.objects.none()
        return AccessCode.objects.filter(
            code_string=code, 
            claimed_user__isnull=True)

    def post(self, request, *args, **kwargs):
        access_code_claim = AccessCodeClaimSerializer(data=request.data)
        access_code_claim.is_valid(raise_exception=True)

        user = get_user_from_request(request)
        if not user:
            return Response(
            {
                "detail": "Authentication required"
            }, 
            status.HTTP_401_UNAUTHORIZED)
        
        code_string = access_code_claim.data.get('code')

        if AccessCode.objects.filter(claimed_user=user).exists():
            return Response(
            {
                "detail": "Already claimed code"
            },
            status.HTTP_400_BAD_REQUEST,
        )

        access_code = AccessCode.objects.get(code_string=code_string)
        access_code.claimed_user = user
        access_code.save()

        Badge.objects.create(
            badge_type=Badge.LOVE_MIST,
            user=user,
        )

        return Response(
            {
                "status": "success",
                "data": access_code_claim.data
            },
            status.HTTP_200_OK,
        )