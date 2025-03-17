'''
views for the user api
'''
from django.contrib.auth import authenticate
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (UserSerializer,
                              AuthTokenSerializer)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the System"""
    serializer_class = UserSerializer

class CreatTokenView(ObtainAuthToken):
    """Create a new auth token view"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrive e and return authenticated user"""
        return self.request.user