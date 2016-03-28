from .models import Follow
from .utils import api, twitter_graph
import twitter
import heapq


class TwitterUser(object):
    '''
    Container object to facilitate working with Twitter Users
    '''

    def __init__(self, full_api_object):
        self.id = full_api_object.id
        self.name = full_api_object.name
        self.screen_name = full_api_object.screen_name
        self.profile_image = full_api_object.profile_image_url
        self.profile_banner = full_api_object.profile_banner_url
        self.followers_count = full_api_object.followers_count
        self.following_count = full_api_object.friends_count
        self.tweets_count = full_api_object.statuses_count
        self.location = full_api_object.location
        self.description = full_api_object.description
        self.profile_background_color = full_api_object.profile_background_color


class OriginalTweet(object):
    '''
    Container object to facilitate working with Tweets within Retweets
    '''

    def __init__(self, retweet_obj):
        self.id = retweet_obj.id
        self.text = retweet_obj.text
        self.created_at = retweet_obj.created_at
        self.user = TwitterUser(retweet_obj.user)


class Tweet(object):
    '''
    Container object to facilitate working with Tweets
    '''

    def __init__(self, api_object):
        self.id = api_object.id
        self.text = api_object.text
        self.created_at = api_object.created_at
        self.user_id = api_object.user.id
        self.user_screen_name = api_object.user.screen_name
        self.media = self.parse_media(api_object.AsDict())
        self.mentions = self.parse_mentions(api_object.AsDict())
        self.urls = self.parse_urls(api_object.AsDict())
        self.original_tweet = self.parse_retweet(api_object.retweeted_status)

    def parse_media(self, dict):
        return dict.get('media', None)

    def parse_urls(self, dict):
        return dict.get('urls', None)

    def parse_mentions(self, dict):
        return dict.get('user_mentions', None)

    def parse_retweet(self, retweet):
        if retweet is None:
            return None
        else:
            return OriginalTweet(retweet)


class Feed(object):
    '''
    Container object to facilitate working with a feed comprised of Tweets from multiple TwitterUsers
    '''

    def __init__(self, user):
        self.user = user
        self.heap = []
        self.lowest_tweet_id = {}
        self.tweets = []
        self.twitter_users = []
        self.follows = Follow.objects.filter(user=user)
        screen_names = [f.screen_name for f in self.follows]
        try:
            # use UserLookup to batch requests to avoid breaking Twitter API rate limit
            self.twitter_users = [TwitterUser(u) for u in api.UsersLookup(screen_name=screen_names)]

        except twitter.TwitterError:
            pass

    def load_new_tweets(self):
        '''
        loads Tweets newer than last_seen from Twitter API for the users contained in the Feed
        '''
        self.load_tweets(True)

    def load_old_tweets(self):
        '''
        loads Tweets earlier than first_seen from Twitter API for the users contained in the Feed
        '''
        self.load_tweets(False)

    def load_tweets(self, is_refresh):
        '''
        helper to load and process tweets into feed
        '''
        # this should be stored as a global in on the user object, but caught the bug too late
        global_min = None
        for follow in self.follows:
            if follow.first_id_seen is not None and global_min is None:
                global_min = follow.first_id_seen
            elif follow.first_id_seen is not None and global_min > follow.first_id_seen:
                global_min = follow.first_id_seen

        for follow in self.follows:
            try:
                if follow.last_id_seen is None and global_min is None:
                    # first pull from timeline all together, don't need since_id
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name)
                elif follow.last_id_seen is None:
                    # first pull from timeline for this user, but not globally - get since global_min
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=global_min, count=80)
                elif is_refresh:
                    # pulling new tweets from timeline
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=follow.last_id_seen)
                else:
                    # pulling old tweets from timeline
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, max_id=follow.first_id_seen - 1)

                if len(timeline) > 0:
                    # convert to container Tweet object and identify newest and oldest Tweet
                    min_id = timeline[0].id
                    for index in xrange(len(timeline)):
                        tweet_obj = Tweet(timeline[index])
                        if tweet_obj.original_tweet is not None:
                            twitter_graph.add_retweet(timeline[index].user.screen_name, tweet_obj.original_tweet.user.screen_name)
                        if tweet_obj.id < min_id:
                            min_id = tweet_obj.id

                        heapq.heappush(self.heap, (-1*tweet_obj.id, tweet_obj))

                    # store minimum tweet id in the dataset for each user so we can tell when we've exhausted the stream
                    self.lowest_tweet_id[follow.screen_name] = min_id

            except twitter.TwitterError:
                pass

    def merge_streams(self):
        '''
        piece-wise merges tweets from multiple users maintaining chronology
        '''
        min_ids = {}
        max_ids = {}

        while self.heap:
            (tweet_id, tweet) = heapq.heappop(self.heap)
            self.tweets.append(tweet)
            if tweet.user_screen_name not in max_ids:
                max_ids[tweet.user_screen_name] = tweet.id

            min_ids[tweet.user_screen_name] = tweet.id
            if tweet.id == self.lowest_tweet_id[tweet.user_screen_name]:
                # reached the end of this data stream, stop iterating to avoid chronology errors
                break

        for f in self.follows:
            # only alter follow data if we pulled a tweet from that stream before exhausting another
            if f.screen_name in max_ids and (f.last_id_seen is None or f.last_id_seen < max_ids[f.screen_name]):
                f.last_id_seen = max_ids[f.screen_name]
            if f.screen_name in min_ids and (f.first_id_seen is None or f.first_id_seen > min_ids[f.screen_name]):
                f.first_id_seen = min_ids[f.screen_name]
            f.save()


