from rest_framework import viewsets, generics
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.generics import get_user_from_request
from users.permissions import UserPermissions
from django.db.models import Q
from django.db.models.expressions import RawSQL

from ..serializers import (
    MatchingPhoneNumberRequestSerializer,
    ReadOnlyUserSerializer,
    CompleteUserSerializer,
)
from ..models import (
    User,
)


class UserView(viewsets.ModelViewSet):
    permission_classes = (UserPermissions, )
    serializer_class = CompleteUserSerializer

    def get_object(self):
        requested_user = super().get_object()
        requesting_user = get_user_from_request(self.request)
        if requesting_user == requested_user:
            self.serializer_class = CompleteUserSerializer
        return requested_user

    def get_queryset(self):
        """
        Returns users matching the username, first_name, last_name
        """
        # parameters
        username = self.request.query_params.get('username')
        first_name = self.request.query_params.get('first_name')
        last_name = self.request.query_params.get('last_name')
        words = self.request.query_params.getlist('words')
        token = self.request.query_params.get('token')
        requesting_user = get_user_from_request(self.request)

        # default is to return all users
        queryset = User.objects.all()

        # filter by words...
        if words:
            for word in words:
                word_in_username = User.objects.filter(username__icontains=word)
                word_in_first_name = User.objects.filter(first_name__icontains=word)
                word_in_last_name = User.objects.filter(last_name__icontains=word)
                word_userset = (word_in_username | word_in_first_name | word_in_last_name).distinct()
                queryset = queryset.intersection(word_userset)
            queryset = User.objects.filter(id__in=queryset.values_list('id'))
        # or username, first_name, and last_name
        elif username or first_name or last_name:
            username_set = User.objects.none()
            first_name_set = User.objects.none()
            last_name_set = User.objects.none()
            if username: 
                username_set = User.objects.filter(username__startswith=username)
            if first_name:
                first_name_set = User.objects.filter(first_name__startswith=first_name)
            if last_name:
                last_name_set = User.objects.filter(last_name__startswith=last_name)
            queryset = (username_set | first_name_set | last_name_set).distinct()
        # or token
        elif token:
            matching_tokens = Token.objects.filter(key=token)
            if not matching_tokens:
                queryset = User.objects.none()
            else:
                matching_token = matching_tokens[0]
                queryset = User.objects.filter(id=matching_token.user.id)

        # set serializers based on requesting user + method
        object_level_methods = ["DELETE", "PUT", "PATCH",]
        if self.request.method in object_level_methods:
            return queryset.exclude(is_hidden=True).prefetch_related('badges', 'collectibles')
        else:
            non_matching_users = ~Q(id=requesting_user.id)
            readonly_users = queryset.filter(non_matching_users)

            if readonly_users:
                self.serializer_class = ReadOnlyUserSerializer
            else:
                self.serializer_class = CompleteUserSerializer

        return queryset.exclude(is_hidden=True).prefetch_related('badges', 'collectibles')

    def create(self, request, *args, **kwargs):
        user_response = super().create(request, *args, **kwargs)
        user_id = user_response.data.get('id')
        token, _ = Token.objects.get_or_create(user_id=user_id)
        content = {
            'token': token.key,
        }
        return Response(content, status.HTTP_201_CREATED)


class MatchingPhoneNumbersView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = MatchingPhoneNumberRequestSerializer

    def create(self, request, *args, **kwargs):
        search_request = MatchingPhoneNumberRequestSerializer(data=request.data)
        search_request.is_valid(raise_exception=True)

        phone_numbers = search_request.data.get('phone_numbers')

        phonebook = {}

        users = User.objects.\
            filter(phone_number__in=phone_numbers).\
            prefetch_related('badges').\
            exclude(is_hidden=True).all()
        
        for user in users:
            phonebook[str(user.phone_number)] = ReadOnlyUserSerializer(user).data
            
        return Response(phonebook, status.HTTP_200_OK)


class NearbyUsersView(generics.ListAPIView):
    permission_classes = (UserPermissions, )
    serializer_class = ReadOnlyUserSerializer

    MAX_DISTANCE = .1

    def get_locations_nearby_coords(self, latitude, longitude, max_distance=MAX_DISTANCE):
        """
        Return objects sorted by distance to specified coordinates
        which distance is less than max_distance given in kilometers
        """
        # Great circle distance formula
        gcd_formula = "6371 * acos(least(greatest(\
        cos(radians(%s)) * cos(radians(latitude)) \
        * cos(radians(longitude) - radians(%s)) + \
        sin(radians(%s)) * sin(radians(latitude)) \
        , -1), 1))"
        distance_raw_sql = RawSQL(
            gcd_formula,
            (latitude, longitude, latitude)
        )
        # make sure the latitude + longtitude exists
        # make sure the distance is under the max
        qs = User.objects.all()\
        .filter(latitude__isnull=False)\
        .filter(longitude__isnull=False)\
        .annotate(distance=distance_raw_sql)\
        .order_by('distance')\
        .exclude(is_hidden=True)
        # distance must be less than max distance
        qs = qs.filter(distance__lt=max_distance)
        return qs

    def get_queryset(self):
        requesting_user = get_user_from_request(self.request)
        nearby_users = self.get_locations_nearby_coords(
            requesting_user.latitude,
            requesting_user.longitude)
        return nearby_users

class UserPopulationView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    
    def retrieve(self, request, *args, **kwargs):
        return Response(
            {
                "population": User.objects.count(),
            },
            status.HTTP_200_OK,
        )