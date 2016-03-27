from django.db import models
from .managers import TokenManager


class Token(models.Model):
    session_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    objects = TokenManager()

    class Meta:
        managed = False
        db_table = 'token'


class User(models.Model):
    token = models.OneToOneField(Token)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'user'


class Follow(models.Model):
    user = models.ForeignKey(User)
    screen_name = models.CharField(max_length=20)
    last_id_seen = models.BigIntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'follow'
