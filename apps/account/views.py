from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import exceptions
from .models import *
from .feed import Tweet, TwitterUser
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
        Method: POST
        Args: None
        '''
        return Response(TokenSerializer(request.user.token).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

    @list_route(methods=['POST'])
    def check_user(self, request):
        '''
        Check if screen_name is valid
        Method: POST
        Args: string screen_name
        '''
        screen_name = request.data.get('screen_name', None)
        try:
            api.GetUser(screen_name=screen_name)
            return Response()
        except twitter.TwitterError:
            # not a valid twitter screen_name
            raise exceptions.NotFound()

    @list_route(methods=['POST'])
    def refresh_tweets(self, request):
        '''
        Refresh twitter data from followees
        Method: POST
        Args: None
        '''
        follows = Follow.objects.filter(user=request.user)
        tweets = []

        for follow in follows:
            try:
                timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=follow.last_id_seen, count=5)
                if len(timeline) > 0:
                    for t in timeline:
                        tweets.append(Tweet(id=t.id, text=t.text))

                    # update follow object with new last tweet id that they've seen
                    follow.last_id_seen = timeline[0].id
                    follow.save()
            except twitter.TwitterError:
                pass

        return Response(TweetSerializer(tweets, many=True).data)

    def create(self, request):
        '''
        Follow a new batch of users
        Method: POST
        Args: JSON object in following format
        {
            "additions": [{
                "screen_name": "{example_screen_name}"
            }, {
                "screen_name": "{example_screen_name_2}"
            }]
        }
        '''
        if 'additions' not in request.data:
            return Response()

        new_follows = []
        for obj in request.data['additions']:
            try:
                twitter_user = TwitterUser(api.GetUser(screen_name=obj['screen_name']))
            except twitter.TwitterError:
                continue

            try:
                Follow.objects.get(screen_name=twitter_user.screen_name, user=request.user)
            except Follow.DoesNotExist:
                # they are not already following this user, add them
                Follow.objects.create(screen_name=twitter_user.screen_name, user=request.user)
                new_follows.append(twitter_user)

        return Response(TwitterUserSerializer(new_follows, many=True).data)
