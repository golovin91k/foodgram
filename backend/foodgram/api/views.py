from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from djoser.views import UserViewSet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination 

from .serializers import CustomUserCreateSerializer, CustomUserSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageNumberPagination 

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        return queryset


    def get_serializer_class(self):
        if self.action in ('post',):
            return CustomUserCreateSerializer
        return CustomUserSerializer
    
"""
class CustomUserListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)
#    http_method_names = ['get', 'list']
"""