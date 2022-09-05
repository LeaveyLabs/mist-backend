from decimal import Decimal
from enum import Enum
from django.db.models.expressions import RawSQL
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from mist.generics import is_impermissible_post
from mist.permissions import PostPermission
from rest_framework.permissions import IsAuthenticated

from mist.serializers import AccessCodeClaimSerializer
from mist.models import AccessCode, Badge
from users.generics import get_user_from_request

class ClaimAccessCodeView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        access_code_claim = AccessCodeClaimSerializer(data=request.data)
        access_code_claim.is_valid(raise_exception=True)

        user = get_user_from_request(request)
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