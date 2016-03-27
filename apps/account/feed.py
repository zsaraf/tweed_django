class TwitterUser(object):
    '''
    Container object to facilitate working with Twitter Users
    '''

    def __init__(self, full_api_object):
        self.id = full_api_object.id
        self.name = full_api_object.name
        self.screen_name = full_api_object.screen_name
        self.profile_image = full_api_object.profile_image_url
        self.profile_background_image = full_api_object.profile_background_image_url
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
        self.original_tweet = self.parse_retweet(api_object.retweeted_status)

    def parse_retweet(self, retweet):
        if retweet is None:
            return None
        else:
            return OriginalTweet(retweet)


class Feed(object):
    '''
    Container object to facilitate working with a feed comprised of Tweets from multiple TwitterUsers
    '''

    def __init__(self):
        self.tweets = []
        self.twitter_users = []

    def add_stream(self, stream):
        if stream is not None:
            self.tweets.extend(stream)

    def add_users(self, users):
        if users is not None:
            self.twitter_users.extend(users)

    def merge_streams(self):
        self.tweets.sort(key=lambda t: t.id, reverse=True)
