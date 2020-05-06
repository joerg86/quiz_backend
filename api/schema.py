from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from api.models import Topic, Team

class TeamNode(DjangoObjectType):
    class Meta:
        model = Team
        filter_fields = ["name"]
        fields = ["name", "state", "mode", "created_at"]
        interfaces = (relay.Node,)

class TopicNode(DjangoObjectType):
    class Meta: 
        model = Topic
        filter_fields = ["code", "name"]
        interfaces = (relay.Node,)
        fields = ["name", "code"]

class Query(ObjectType):
    team = relay.Node.Field(TeamNode)
    topic = relay.Node.Field(TopicNode)

    topics = DjangoFilterConnectionField(TopicNode)
    teams = DjangoFilterConnectionField(TeamNode)

