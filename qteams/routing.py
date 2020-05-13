from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path 
from channels.auth import AuthMiddlewareStack

from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer

application = AuthMiddlewareStack(ProtocolTypeRouter({
    "websocket": URLRouter([
        path('', GraphqlSubscriptionConsumer)
    ]),
}))