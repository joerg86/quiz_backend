from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path 
from .auth import JWTAuthMiddlewareStack
from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer

application = ProtocolTypeRouter({
    "websocket": (JWTAuthMiddlewareStack(URLRouter([
        path('', GraphqlSubscriptionConsumer)
    ]))),
})