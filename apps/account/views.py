from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from .models import *
from .serializers import *
from django.conf import settings
import twitter

api = twitter.Api(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.CONSUMER_SECRET,
            access_token_key=settings.ACCESS_TOKEN,
            access_token_secret=settings.ACCESS_SECRET
        )


class TokenViewSet(viewsets.ModelViewSet):
    queryset = Token.objects.all()
    serializer_class = TokenSerializer

    def create(self, request):
        '''
        Create a new Token
        '''
        return Response(TokenSerializer(request.user.token).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

    @list_route(methods=['POST'])
    def refresh_tweets(self, request):
        '''
        Refresh twitter data from followees
        '''
        follows = Follow.objects.filter(user=request.user)
        tweets = []

        for follow in follows:
            timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=follow.last_id_seen, count=5)
            tweets.append(t.AsJsonString() for t in timeline)

        return Response(tweets)

    def create(self, request):
        '''
        Follow a new batch of users
        '''
        if 'additions' not in request.data:
            return Response()

        new_follows = []
        for obj in request.data['additions']:
            try:
                twitter_user = api.GetUser(screen_name=obj['screen_name'])
            except twitter.TwitterError:
                continue

            try:
                Follow.objects.get(screen_name=twitter_user.screen_name, user=request.user)
            except Follow.DoesNotExist:
                # they are not already following this user, add them
                follow = Follow.objects.create(screen_name=twitter_user.screen_name, user=request.user)
                new_follows.append(follow)

        return Response(FollowSerializer(new_follows, many=True).data)
