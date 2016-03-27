from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import exceptions
from .models import *
from .feed import Tweet, TwitterUser, Feed
from .graph import TwitterGraph
from .serializers import *
from django.conf import settings
import twitter

api = twitter.Api(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.CONSUMER_SECRET,
            access_token_key=settings.ACCESS_TOKEN,
            access_token_secret=settings.ACCESS_SECRET
        )

twitter_graph = TwitterGraph()


class TokenViewSet(viewsets.ModelViewSet):
    queryset = Token.objects.all()
    serializer_class = TokenSerializer

    def create(self, request):
        '''
        Create a new Token
        Method: POST
        Args: None
        '''
        twitter_graph.add_user(request.user)
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
        screen_names = []
        feed = Feed()

        for follow in follows:
            tweets = []
            screen_names.append(follow.screen_name)
            try:
                if follow.last_id_seen is None:
                    # first pull from timeline, include count instead of since_id
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, count=5)
                else:
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=follow.last_id_seen)

                if len(timeline) > 0:
                    # convert to container Tweet object and identify newest Tweet
                    max_id = follow.last_id_seen
                    for t in timeline:
                        tweets.append(Tweet(id=t.id, text=t.text, created_at=t.created_at, user_id=t.user.id))
                        if t.id > max_id:
                            max_id = t.id

                    # add this TwitterUsers twitter stream to feed object
                    feed.add_stream(tweets)

                    # update follow object with new last tweet id that they've seen
                    follow.last_id_seen = max_id
                    follow.save()
            except twitter.TwitterError:
                pass

        try:
            # use UserLookup to batch requests to avoid breaking Twitter API rate limit
            users = [TwitterUser(u) for u in api.UsersLookup(screen_name=screen_names)]
            feed.add_users(users)

        except twitter.TwitterError:
            feed.add_users(None)

        feed.merge_streams()
        return Response(FeedSerializer(feed).data)


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

        return Response(suggested_users)

    @list_route(methods=['GET'])
    def check_user(self, request):
        '''
        Check if screen_name is valid
        Method: GET
        Args: string screen_name
        '''
        screen_name = request.GET.get('screen_name', None)

        # check if we've already cached that TwitterUser in our graph
        if twitter_graph.is_cached(screen_name):
            return Response()

        try:
            api.GetUser(screen_name=screen_name)
            twitter_graph.add_twitter_user(screen_name)
            return Response()
        except twitter.TwitterError:
            # not a valid twitter screen_name
            raise exceptions.NotFound()

    @list_route(methods=['POST'])
    def edit(self, request):
        '''
        Follow a new batch of users
        Method: POST
        Args: JSON object in following format
        {
            "additions": ["screen_name_1", "screen_name_2"]
            "deletions": ["screen_name_3", "screen_name_4"]
        }
        '''
        if 'deletions' in request.data:

            for screen_name in request.data['deletions']:
                try:
                    Follow.objects.get(screen_name=screen_name, user=request.user).delete()
                    twitter_graph.remove_follow(screen_name, request.user)
                except Follow.DoesNotExist:
                    pass

        if 'additions' in request.data and len(request.data['additions']) > 0:

            new_follows = []
            screen_names = request.data['additions']

            try:
                # use UserLookup to batch requests to avoid breaking Twitter API rate limit
                users = api.UsersLookup(screen_name=screen_names)
            except twitter.TwitterError:
                return Response("Invalid Twitter username", 500)

            for u in users:
                twitter_user = TwitterUser(u)

                try:
                    Follow.objects.get(screen_name=twitter_user.screen_name, user=request.user)
                except Follow.DoesNotExist:
                    # they are not already following this user, add them
                    Follow.objects.create(screen_name=twitter_user.screen_name, user=request.user)
                    twitter_graph.add_follow(twitter_user.screen_name, request.user)
                    new_follows.append(twitter_user)

            return Response(TwitterUserSerializer(new_follows, many=True).data)

        return Response()
