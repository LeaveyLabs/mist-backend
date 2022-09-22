from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.generics import get_user_from_request

from ..serializers import CollectibleSerializer
from ..models import Collectible

class ClaimCollectibleView(generics.CreateAPIView):
    permission_classes = IsAuthenticated
    serializer_class = CollectibleSerializer

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        request.data.update({"user": f"{user.id}"})

        collectible_claim = CollectibleSerializer(data=request.data)
        collectible_claim.is_valid(raise_exception=True)

        collectible_type = collectible_claim.data.get('collectible_type')

        if Collectible.objects.filter(
            collectible_type=collectible_type,
            user=user).exists():
            return Response(
                {
                    "detail": "Already claimed collectible",
                },
                status.HTTP_400_BAD_REQUEST)
        
        Collectible.objects.create(
            collectible_type=collectible_type,
            user=user,
        )

        return Response(
            {
                "status": "success",
                "data": collectible_claim.data
            },
            status.HTTP_201_CREATED,
        )