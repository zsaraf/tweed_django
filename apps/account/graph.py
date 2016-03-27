from py2neo import Graph, Node, Relationship


class TwitterGraph():

    def __init__(self):
        self.graph = Graph("http://neo4j:Eabltf1!@54.191.171.209:7474/db/data/")

    def add_user(self, user):
        new_user = Node("User", token=user.token.session_id, user_id=user.id)
        self.graph.create(new_user)

    def is_cached(self, screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is not None:
            return True

    def add_twitter_user(self, screen_name):
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        if twitter_user is None:
            new_twitter_user = Node("TwitterUser", screen_name=screen_name)
            self.graph.create(new_twitter_user)

    def add_follow(self, screen_name, user_id):
        user = self.graph.find_one("User", 'user_id', user_id)
        twitter_user = self.graph.find_one("TwitterUser", 'screen_name', screen_name)
        follow_relationship = Relationship(user, "FOLLOWS", twitter_user)
        self.graph.create(follow_relationship)


