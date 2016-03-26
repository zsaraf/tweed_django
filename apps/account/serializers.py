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


class TweetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField(max_length=141)


class TwitterUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=141)
    screen_name = serializers.CharField(max_length=20)
    profile_image = serializers.CharField(max_length=250)
    profile_background_image = serializers.CharField(max_length=250)
    followers_count = serializers.IntegerField()
    location = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=250)
    profile_background_color = serializers.CharField(max_length=250)
