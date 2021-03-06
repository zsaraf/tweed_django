from rest_framework import serializers
from .models import *
import json

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


class TwitterUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=141)
    screen_name = serializers.CharField(max_length=20)
    profile_image = serializers.CharField(max_length=250)
    profile_banner = serializers.CharField(max_length=250)
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    tweets_count = serializers.IntegerField()
    location = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=250)
    profile_background_color = serializers.CharField(max_length=250)


class OriginalTweetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField(max_length=141)
    created_at = serializers.CharField(max_length=100)
    user = TwitterUserSerializer()


class TweetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    text = serializers.CharField(max_length=141)
    created_at = serializers.CharField(max_length=100)
    media = serializers.SerializerMethodField()
    original_tweet = OriginalTweetSerializer()
    mentions = serializers.SerializerMethodField()
    urls = serializers.SerializerMethodField()
    
    def get_media(self, object):
        return object.media

    def get_urls(self, object):
        return object.urls

    def get_mentions(self, object):
        return object.mentions


class FeedSerializer(serializers.Serializer):
    tweets = TweetSerializer(many=True)
    twitter_users = TwitterUserSerializer(many=True)
