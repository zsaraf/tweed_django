from .models import Follow
from .utils import api, twitter_graph
import twitter


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

        for follow in self.follows:
            tweets = []
            try:
                if follow.last_id_seen is None and is_refresh:
                    # first pull from timeline, include count instead of since_id
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, count=5)
                elif is_refresh:
                    # pulling new tweets from timeline
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, since_id=follow.last_id_seen)
                else:
                    # pulling old tweets from timeline
                    timeline = api.GetUserTimeline(screen_name=follow.screen_name, max_id=follow.first_id_seen - 1)

                if len(timeline) > 0:
                    # convert to container Tweet object and identify newest and oldest Tweet
                    max_id = follow.last_id_seen
                    min_id = timeline[0].id
                    for t in timeline:
                        tweet_obj = Tweet(t)
                        if tweet_obj.original_tweet is not None:
                            twitter_graph.add_retweet(t.user.screen_name, tweet_obj.original_tweet.user.screen_name)
                        tweets.append(tweet_obj)
                        if t.id > max_id:
                            max_id = t.id
                        if t.id < min_id:
                            min_id = t.id

                    # add this TwitterUsers twitter stream to feed object
                    self.tweets.extend(tweets)

                    # update follow object with new last tweet id that they've seen
                    follow.last_id_seen = max_id
                    follow.first_id_seen = min_id
                    follow.save()
            except twitter.TwitterError:
                pass

    def merge_streams(self):
        '''
        sorts the Tweets into reverse chronological order
        '''
        self.tweets.sort(key=lambda t: t.id, reverse=True)

