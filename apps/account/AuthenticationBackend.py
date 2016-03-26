from rest_framework import authentication
from rest_framework import exceptions
from .models import User, Token
import os


class TweedAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        session_id = request.META.get('HTTP_X_SESSION_ID')
        if not session_id:
            # user doesn't have a token yet
            if self.is_create_token(request):
                # they were attempting to login, so call to create a new user object for them
                token = Token.objects.generate_new_token()
                user = User.objects.create(token=token)
            else:
                raise exceptions.AuthenticationFailed('Invalid token')

        else:
            try:
                # user has a token already, just fetch existing user object
                token = Token.objects.get(session_id=session_id)
                user = User.objects.get(token=token)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed('No such user')
            except Token.DoesNotExist:
                raise exceptions.AuthenticationFailed('Invalid token')

        return (user, token)

    def is_create_token(self, request):
        return request.method == "POST" and os.path.basename(os.path.normpath(request.path)) == "tokens"
