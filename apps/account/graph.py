from py2neo import Graph, Node, Relationship
from collections import Counter
import heapq


class TwitterGraph():

    def __init__(self):
        self.graph = Graph("http://neo4j:Eabltf1!@54.191.171.209:7474/db/data/")
        self.popularity_heap = []
        self.reassess_popularity()

    def add_user(self, user):
        new_user = Node("User", token=user.token.session_id, user_id=user.id)
        return self.graph.create(new_user)

    def is_cached(self, screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is not None:
            return True

    def get_RT_recommendations(self, user):
        recommendations = Counter()
        user_node = self.graph.find_one("User", 'user_id', user.id)
        following = user_node.match_outgoing("FOLLOWS", limit=5)

        for rel in following:
            retweets = rel.end_node.match_outgoing("RETWEETED", limit=5)
            for r in retweets:
                recommendations[r.end_node.properties['screen_name']] += 1

        return [str for (str, count) in recommendations.most_common(10)]

    def get_generic_recommendations(self):
        return [screen_name for (count, screen_name) in heapq.nlargest(10, self.popularity_heap)]

    def reassess_popularity(self):
        # NOTE: expensive calculation, to be run threaded at multiples of x actions to graph or hourly/daily job
        all_twitter_users = self.graph.find("TwitterUser")
        for tu in all_twitter_users:
            incoming_count = sum(1 for _ in tu.match_incoming())
            heapq.heappush(self.popularity_heap, (incoming_count, tu.properties['screen_name']))

    def add_twitter_user(self, screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is None:
            new_twitter_user = Node("TwitterUser", screen_name=screen_name)
            self.graph.create(new_twitter_user)

    def add_follow(self, screen_name, user):
        user_node = self.graph.find_one("User", 'user_id', user.id)
        if user_node is None:
            # this shouldn't happen, just for testing while transitioning db
            self.add_user(user)
            user_node = self.graph.find_one("User", 'user_id', user.id)

        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is None:
            # this shouldn't happen, just for testing while transitioning db
            self.add_twitter_user(screen_name)
            twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)

        follow_relationship = Relationship(user_node, "FOLLOWS", twitter_user)
        self.graph.create(follow_relationship)
        self.reassess_popularity()

    def remove_follow(self, screen_name, user):
        user_node = self.graph.find_one("User", 'user_id', user.id)
        if user_node is None:
            # this shouldn't happen, just for testing while transitioning db
            self.add_user(user)
            user_node = self.graph.find_one("User", 'user_id', user.id)

        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is None:
            # this shouldn't happen, just for testing while transitioning db
            self.add_twitter_user(screen_name)
            twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)

        follow_relationship = self.graph.match_one(user_node, "FOLLOWS", twitter_user)
        if follow_relationship is not None:
            self.graph.delete(follow_relationship)

    def add_retweet(self, screen_name, retweeted_screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is None:
            # this shouldn't happen, just for testing while transitioning db
            self.add_twitter_user(screen_name)
            twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)

        self.add_twitter_user(retweeted_screen_name)
        retweeted_twitter_user = self.graph.find_one("TwitterUser", 'screen_name', retweeted_screen_name)

        retweet = self.graph.match_one(twitter_user, "RETWEETED", retweeted_twitter_user)
        if retweet is None:
            retweet_relationship = Relationship(twitter_user, "RETWEETED", retweeted_twitter_user)
            retweet_relationship.properties['count'] = 1
            self.graph.create(retweet_relationship)
        elif retweet.properties['count'] is None:
            # this shouldn't happen, just for testing while transitioning db
            retweet.properties['count'] = 1
            retweet.push()
        else:
            retweet.properties['count'] = retweet.properties['count'] + 1
            retweet.push()

