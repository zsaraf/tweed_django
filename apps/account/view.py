from rest_framework import viewsets
from .models import *
from .serializers import *


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

    def create(self, request):
        '''
        Follow a new batch of users
        '''