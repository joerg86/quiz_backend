from django.db import close_old_connections
from django.contrib.auth import authenticate, login
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_user_by_token
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from channels.sessions import SessionMiddleware, CookieMiddleware
from channels.auth import UserLazyObject


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for Graphene JWT
    """

    def populate_scope(self, scope):
        # Add it to the scope if it's not there already
        if "user" not in scope:
            scope["user"] = UserLazyObject()

    async def resolve_scope(self, scope):
        token = scope.get("query_string")

        if token and token.startswith(b"auth="):
            token = token.replace(b"auth=", b"")
            token = token.decode("ascii")
            user = await database_sync_to_async(get_user_by_token)(token)
        else:
            user = AnonymousUser()
        
        scope["user"]._wrapped = user

        return self.inner(dict(scope, user=user))

# Handy shortcut for applying all three layers at once
JWTAuthMiddlewareStack = lambda inner: CookieMiddleware(
    SessionMiddleware(JWTAuthMiddleware(inner))
)