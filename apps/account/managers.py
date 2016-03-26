from django.db import models
from django.utils.crypto import get_random_string


class TokenManager(models.Manager):

    def generate_new_token(self):
        '''
        Creates a new, unique access string
        '''
        while True:
            unique_string = get_random_string(length=32)

            if self.model.objects.filter(session_id=unique_string).count() == 0:
                token = self.model(
                    session_id=unique_string
                )
                token.save()
                return token
