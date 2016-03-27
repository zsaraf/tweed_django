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

    @list_route(methods=['POST'])
    def refresh(self, request):
        '''
        Refresh data for user, including TwitterUser and Tweet objects linked to their followees
        Method: POST
        Args: None
        '''
        follows = Follow.objects.filter(user=request.user)
        tweets = []

        for follow in follows:
            try:
                if follow.last_id_seen is None:
                    # first pull from timeline, include count instead of since_id
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, count=5)
                else:
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=follow.last_id_seen)

                if len(timeline) > 0:
                    max_id = follow.last_id_seen
                    for t in timeline:
                        tweets.append(Tweet(id=t.id, text=t.text))
                        if t.id > follow.last_id_seen:
                            max_id = t.id

                    # update follow object with new last tweet id that they've seen
                    follow.last_id_seen = max_id
                    follow.save()
                    return Response(max_id)
            except twitter.TwitterError:
                pass

        return Response(TweetSerializer(tweets, many=True).data)


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

    @list_route(methods=['GET'])
    def get_suggestions(self, request):
        '''
        Get suggested TwitterUsers to follow
        Method: GET
        Args: none
        '''
        suggested_users = []
        screen_names = ['taylorswift13', 'justinbieber', 'tim_cook', 'BarackObama', 'YouTube', 'rihanna', 'TheEllenShow', 'KimKardashian', 'Cristiano', 'cnnbrk', 'Oprah']
        try:
            # use UserLookup to batch requests to avoid breaking Twitter API rate limit
            users = api.UsersLookup(screen_name=screen_names)
            for u in users:
                suggested_users.append(TwitterUserSerializer(TwitterUser(u)).data)

        except twitter.TwitterError:
            return Response("We're experiencing difficulties, please try again later!", 500)

        # trends = api.GetTrendsWoeid(23424977)
        # for i in xrange(min(5, len(trends))):
        #     trend = trends[i]
        #     trending_tweets = api.GetSearch(term=trend.name, lang='en', result_type='popular')
        #     for t in trending_tweets:
        #         if t.user.screen_name not in suggested_users:
        #             suggested_users[t.user.screen_name] = TwitterUserSerializer(TwitterUser(t.user)).data

        return Response(strs)

    @list_route(methods=['GET'])
    def check_user(self, request):
        '''
        Check if screen_name is valid
        Method: GET
        Args: string screen_name
        '''
        screen_name = request.GET.get('screen_name', None)
        try:
            api.GetUser(screen_name=screen_name)
            return Response()
        except twitter.TwitterError:
            # not a valid twitter screen_name
            raise exceptions.NotFound()

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
        screen_names = request.data['additions']

        try:
            # use UserLookup to batch requests to avoid breaking Twitter API rate limit
            users = api.UsersLookup(screen_name=screen_names)
        except twitter.TwitterError:
            return Response("Inavlid Twitter username", 500)

        for u in users:
            twitter_user = TwitterUser(u)

            try:
                Follow.objects.get(screen_name=twitter_user.screen_name, user=request.user)
            except Follow.DoesNotExist:
                # they are not already following this user, add them
                Follow.objects.create(screen_name=twitter_user.screen_name, user=request.user)
                new_follows.append(twitter_user)

        return Response(TwitterUserSerializer(new_follows, many=True).data)
