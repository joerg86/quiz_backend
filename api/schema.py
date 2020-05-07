from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from api.models import Topic, Team, Round, Question, Answer
from django.contrib.auth.models import User
import graphene
from rx import Observable

class Subscription(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return Observable.interval(3000) \
                         .map(lambda i: "hello world!")

class OtherUserNode(DjangoObjectType):
    class Meta:
        model = User
        fields = ["username", "last_name", "first_name"]

class RoundNode(DjangoObjectType):
    class Meta:
        model = Round
        interfaces = (relay.Node,)
        fields = ["state", "current_question", "created_at", "question_set"]

class QuestionNode(DjangoObjectType):
    class Meta:
        model = Question
        fields = ("question", "model_answer", "author")
        filter_fields = ("question", "model_answer")
        interfaces = (relay.Node,)

class TeamNode(DjangoObjectType):
    class Meta:
        model = Team
        filter_fields = ["name"]
        fields = ("name", "state", "mode", "created_at", "creator", "round_set", "topic")
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
    questions = DjangoFilterConnectionField(QuestionNode)
    teams = DjangoFilterConnectionField(TeamNode)

