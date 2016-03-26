from rest_framework import serializers
from .models import *


class TokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Token
        fields = ['session_id']


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id']


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
