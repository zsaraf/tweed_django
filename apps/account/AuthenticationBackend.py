from rest_framework import authentication
from rest_framework import exceptions
from .models import User, Token


class TweedAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_X_SESSION_ID')

        if not token:
            # if the user doesn't have a token yet, assign one and create new user in db
            token = Token.objects.generate_new_token()
            user = User.objects.create(token=token)

        try:
            # user has a token already, just fetch existing user object
            user = User.objects.get(token=token)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        return (user, token)
