from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from api.models import Topic, Team, Question, Answer
from django.contrib.auth.models import User
import graphene
from rx import Observable
from graphql_relay import from_global_id
from graphql_jwt.decorators import login_required
from graphene_subscriptions.events import UPDATED 
from django.core.exceptions import PermissionDenied
import django_filters
from django.db.models import Q

class UserNode(DjangoObjectType):
    is_me = graphene.Boolean()

    def resolve_is_me(parent, info):
        return info.context.user == parent

    class Meta:
        model = User
        fields = ["username", "last_name", "first_name", "id"]
        filter_fields = {
            "username": ["icontains"]
        }
        interfaces = (relay.Node,)

class AnswerNode(DjangoObjectType):
    class Meta:
        model = Answer
        fields = ("author", "answer", "score")
        interfaces = (relay.Node,)

class QuestionNode(DjangoObjectType):
    class Meta:
        model = Question
        fields = ("question", "model_answer", "author", "answer_set")
        filter_fields = ("question", "model_answer")
        interfaces = (relay.Node,)


class TeamNode(DjangoObjectType):
    user_done = graphene.Boolean()

    def resolve_user_done(parent, info):
        return parent.user_done(info.context.user)

    class Meta:
        model = Team
        filter_fields = ["name"]
        fields = ("name", "state", "mode", "created_at", "creator", "topic", "state", "current_question", "members")
        interfaces = (relay.Node,)

class TopicFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="query_filter")

    def query_filter(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(code__icontains=value)).distinct()

    class Meta:
        model = Topic
        fields = ("name", "code")

class TopicNode(DjangoObjectType):
    class Meta: 
        model = Topic
        interfaces = (relay.Node,)
        fields = ["name", "code"]


class Subscription(graphene.ObjectType):
    team_updated = graphene.Field(TeamNode, id=graphene.ID())

    @login_required
    def resolve_team_updated(root, info, id):
        return root.filter(
            lambda event:
                event.operation == UPDATED and
                isinstance(event.instance, Team) and
                event.instance.pk == int(from_global_id(id)[1])
        ).map(lambda event: event.instance)

class NextPhaseMutation(relay.ClientIDMutation):
    """Switch to the next phase of the team"""
    class Input:
        id = graphene.ID(required=True)

    team = graphene.Field(TeamNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        team = Team.objects.get(pk=from_global_id(id)[1])
        team.next_state()
        return NextPhaseMutation(team=team)
       
class PostQuestionMutation(relay.ClientIDMutation):
    """Post a question to the current team"""
    class Input:
        id = graphene.ID(required=True)
        question = graphene.String(required=True)
        model_answer = graphene.String(required=True)

    team = graphene.Field(TeamNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, id, question, model_answer):
        team = Team.objects.get(pk=from_global_id(id)[1])

        if team.get_user_question(info.context.user):
            raise PermissionDenied("Es wurde bereits eine Frage erstellt")

        team.questions.create(
            author=info.context.user,
            question=question,
            model_answer=model_answer,
            topic=team.topic,
        )

        if team.questions.count() == team.members.count():
            team.current_question = team.questions.first()
            team.state = "answer"

        team.save()

        return PostQuestionMutation(team=team)

       
class PostAnswerMutation(relay.ClientIDMutation):
    """Post an answer to the current question"""
    class Input:
        id = graphene.ID(required=True)
        answer = graphene.String(required=True)

    team = graphene.Field(TeamNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, id, answer):
        team = Team.objects.get(pk=from_global_id(id)[1])

        team.current_question.answer_set.create(
            author=info.context.user,
            answer=answer
        )

        if team.current_question.answer_set.count() == team.members.count() - 1:
            team.state = "scoring"

        team.save()

        return PostAnswerMutation(team=team)

class ScoreEnum(graphene.Enum):
    RIGHT = 3
    PARTIAL = 1
    WRONG = 0

class ScoreAnswerMutation(relay.ClientIDMutation):
    """Give a score to an answer"""
    class Input:
        id = graphene.ID(required=True)
        score = ScoreEnum()
    
    answer = graphene.Field(AnswerNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, id, score):
        answer = Answer.objects.get(pk=from_global_id(id)[1])
        answer.score = score
        answer.save()
        for team in answer.question.team_set.all():
            team.save()


        return ScoreAnswerMutation(answer=answer)

class CreateTeamMutation(relay.ClientIDMutation):
    """Create a team"""
    class Input:
        name = graphene.String(required=True)
        topic_id = graphene.ID(required=True)
    
    team = graphene.Field(TeamNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, name, topic_id):
        topic_id = from_global_id(topic_id)[1]
        team = Team.objects.create(creator=info.context.user, name=name, topic_id=topic_id)
        team.members.add(info.context.user)
        return CreateTeamMutation(team=team)

class AddMemberMutation(relay.ClientIDMutation):
    """Add a member to a team"""
    class Input:
        team_id = graphene.ID(required=True)
        username = graphene.String(required=True)

    team = graphene.Field(TeamNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, team_id, username):
        team = Team.objects.get(pk=from_global_id(team_id)[1])
        user = User.objects.get(username=username)
        team.members.add(user)
        team.save()
        return AddMemberMutation(team=team)

class Mutation(ObjectType):
    next_phase = NextPhaseMutation.Field()
    post_question = PostQuestionMutation.Field()
    post_answer = PostAnswerMutation.Field()
    score_answer = ScoreAnswerMutation.Field()
    create_team = CreateTeamMutation.Field()
    add_member = AddMemberMutation.Field()


class Query(ObjectType):
    team = relay.Node.Field(TeamNode)
    topic = relay.Node.Field(TopicNode)

    topics = DjangoFilterConnectionField(TopicNode, filterset_class=TopicFilter)
    questions = DjangoFilterConnectionField(QuestionNode)
    teams = DjangoFilterConnectionField(TeamNode)
    users = DjangoFilterConnectionField(UserNode)

    me = graphene.Field(UserNode)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None