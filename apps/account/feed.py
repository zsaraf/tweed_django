class Tweet(object):
    '''
    Container object to facilitate working with Tweets
    '''

    def __init__(self, id, text):
        self.id = id
        self.text = text


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
        self.location = full_api_object.location
        self.description = full_api_object.description
        self.profile_background_color = full_api_object.profile_background_color


class Feed(object):
    '''
    Container object to facilitate working with a feed comprised of Tweets from multiple TwitterUsers
    '''