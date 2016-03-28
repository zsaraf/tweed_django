import twitter
from .graph import TwitterGraph
from django.conf import settings

api = twitter.Api(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.CONSUMER_SECRET,
            access_token_key=settings.ACCESS_TOKEN,
            access_token_secret=settings.ACCESS_SECRET
        )

twitter_graph = TwitterGraph()
