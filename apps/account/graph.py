from py2neo import Graph, Node, Relationship


class TwitterGraph():

    def __init__(self):
        self.graph = Graph("http://neo4j:Eabltf1!@54.191.171.209:7474/db/data/")

    def add_user(self, user):
        new_user = Node("User", token=user.token.session_id, user_id=user.id)
        return self.graph.create(new_user)

    def is_cached(self, screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is not None:
            return True

    def add_twitter_user(self, screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is None:
            new_twitter_user = Node("TwitterUser", screen_name=screen_name)
            return self.graph.create(new_twitter_user)
        else:
            return twitter_user

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

        retweet_relationship = Relationship(twitter_user, "RETWEETED", retweeted_twitter_user)
        self.graph.create(retweet_relationship)

