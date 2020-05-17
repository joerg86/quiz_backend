from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from api.models import Topic, Team, Question, Answer, Membership
from django.contrib.auth.models import User
import graphene
from rx import Observable
from graphql_relay import from_global_id
from graphql_jwt.decorators import login_required
from graphene_subscriptions.events import UPDATED 
from django.core.exceptions import PermissionDenied
import django_filters
from django.db.models import Q, Count, Case, When, IntegerField

class UserNode(DjangoObjectType):
    is_me = graphene.Boolean()

    def resolve_is_me(parent, info):
        return info.context.user == parent

    class Meta:
        model = User
        fields = ["username", "last_name", "first_name", "id","email"]
        filter_fields = {
            "username": ["icontains"]
        }
        interfaces = (relay.Node,)

class AnswerNode(DjangoObjectType):
    class Meta:
        model = Answer
        fields = ("author", "answer", "score")
        interfaces = (relay.Node,)

class QuestionFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="query_filter")
    own = django_filters.BooleanFilter(method="own_filter")

    def query_filter(self, queryset, name, value):
        return queryset.filter(Q(question__icontains=value) | Q(model_answer__icontains=value)).distinct()

    def own_filter(self, queryset, name, value):
        if value:
            return queryset.filter(author=self.request.user)
        else:
            return queryset

    class Meta:
        model = Question
        fields = ["topic"]


class QuestionNode(DjangoObjectType):
    class Meta:
        model = Question
        fields = ("question", "model_answer", "author", "answer_set", "topic")

        interfaces = (relay.Node,)




class MembershipNode(DjangoObjectType):
    score = graphene.Int()

    def resolve_score(parent, info):
        return parent.get_score()

    class Meta:
        model = Membership
        fields = ["user", "right", "wrong", "partial", "joined"]
        interfaces = (relay.Node,)


class TeamNode(DjangoObjectType):
    user_done = graphene.Boolean()
    question_count = graphene.Int()
    question_number = graphene.Int()

    def resolve_question_number(parent, info):
        if hasattr(parent, "question_number"):
            return parent.question_number
        else:
            return parent.questions.filter(done=True).count() + 1

    def resolve_question_count(parent, info):
        if hasattr(parent, "question_count"):
            return parent.question_count
        else:
            return parent.questions.count()

    def resolve_user_done(parent, info):
        return parent.user_done(info.context.user)

    class Meta:
        model = Team
        filter_fields = ["name"]
        fields = ("name", "state", "mode", "created_at", "creator", "topic", "state", "current_question", "members", "membership_set")
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        team = Team.objects.get(pk=id)
        if info.context.user not in team.members.all():
            raise PermissionDenied("Benutzer nicht in diesem Team.")
        return team

class TopicFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="query_filter")

    def query_filter(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(code__icontains=value)).distinct()

    class Meta:
        model = Topic
        fields = {
            "name": ["exact"],
            "code": ["exact"],
        }

    order_by = django_filters.OrderingFilter(
        fields=(
            ("question_count", "questionCount"),
        )
    )

    @property
    def qs(self):
        # The query context can be found in self.request.
        return super(TopicFilter, self).qs.annotate(
            question_count=Count("question"),
        )


class TopicNode(DjangoObjectType):
    question_count = graphene.Int()

    def resolve_question_count(parent, info):
        return getattr(parent, "question_count", None)

    class Meta: 
        model = Topic
        interfaces = (relay.Node,)
        fields = ["name", "code"]


class Subscription(graphene.ObjectType):
    team_updated = graphene.Field(TeamNode, id=graphene.ID())


    @login_required
    def resolve_team_updated(root, info, id):
        team = Team.objects.get(pk=from_global_id(id)[1])
        if info.context.user not in team.members.all():
            raise PermissionDenied("Benutzer nicht im Team.")

        def map_event(event):
            team = event.instance
            if info.context.user not in team.members.all():
                raise PermissionDenied("Benutzer nicht im Team.")
            return team

        return root.filter(
            lambda event:
                event.operation == UPDATED and
                isinstance(event.instance, Team) and
                event.instance.pk == int(from_global_id(id)[1])
        ).map(map_event)

class NextPhaseMutation(relay.ClientIDMutation):
    """Switch to the next phase of the team"""
    class Input:
        id = graphene.ID(required=True)

    team = graphene.Field(TeamNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        team = Team.objects.get(pk=from_global_id(id)[1])

        if team.state == "scoring":
            if team.current_question.author != info.context.user:
                raise PermissionDenied("Nur der Fragesteller kann die Phase abschließen")
        else:
            if team.creator != info.context.user:
                raise PermissionDenied("Nur der Ersteller des Teams kann die Phase abschließen.")

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

class UpdateQuestionMutation(relay.ClientIDMutation):
    """Update a question"""
    class Input:
        id = graphene.ID(required=True)
        question = graphene.String(required=True)
        model_answer = graphene.String(required=True)

    question = graphene.Field(QuestionNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, id, question, model_answer):
        q = Question.objects.get(pk=from_global_id(id)[1])

        if not q.author == info.context.user:
            raise PermissionDenied("Du darfst nur deine eigenen Fragen bearbeiten.")

        q.question = question
        q.model_answer = model_answer

        q.save()
        return UpdateQuestionMutation(question=q)


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
        if answer.question.author != info.context.user:
            raise PermissionDenied("Du musst Fragesteller sein, um diese Antwort zu bewerten.")

        answer.score = score
        answer.save()
        answer.question.team.save()

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

        if team.creator != info.context.user:
            raise PermissionDenied("Nur der Teamersteller kann Mitglieder hinzufügen.")
        if team.state not in ["done", "open"]:
            raise PermissionDenied("In dieser Phase können keine Mitglieder hinzugefügt werden.")
            
        user = User.objects.get(username=username)
        team.members.add(user)
        team.save()
        return AddMemberMutation(team=team)

class RemoveMemberMutation(relay.ClientIDMutation):
    """Remove a member from a team"""
    class Input:
        team_id = graphene.ID(required=True)
        username = graphene.String()

    team = graphene.Field(TeamNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, team_id, username):
        team = Team.objects.get(pk=from_global_id(team_id)[1])

        if username:
            user = User.objects.get(username=username)
        else:
            user = info.context.user

        if team.creator != info.context.user and user != info.context.user:
            raise PermissionDenied("Nur der Teamersteller kann Mitglieder entfernen.")
        if team.state not in ["done", "open"]:
            raise PermissionDenied("In dieser Phase können keine Mitglieder entfernt werden.")

        if user == team.creator and team.members.count() > 1:
            raise PermissionDenied("Entferne erst alle anderen Mitglieder, bevor du das Team verlassen kannst.")

        team.members.remove(user)
        team.save()

        if user == team.creator:
            team.delete()

        return RemoveMemberMutation(team=team)

class RemoveQuestionMutation(relay.ClientIDMutation):
    """Remove a member from a team"""
    class Input:
        id = graphene.ID(required=True)

    question = graphene.Field(QuestionNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, id):
        question = Question.objects.get(pk=from_global_id(id)[1])

        if not question.author == info.context.user:
            raise PermissionDenied("Du kannst nur deine eigenen Fragen löschen.")

        question.delete()

        return RemoveQuestionMutation(question=question)


class ModeEnum(graphene.Enum):
    TRAIN = "train"
    COMPETITION = "competition"

class SetModeMutation(relay.ClientIDMutation):
    """Set mode of the team"""
    class Input:
        team_id = graphene.ID(required=True)
        mode = ModeEnum(required=True)

    team = graphene.Field(TeamNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, team_id, mode):
        team = Team.objects.get(pk=from_global_id(team_id)[1])

        if team.creator != info.context.user:
            raise PermissionDenied("Nur der Teamersteller kann den Modus ändern.")
        if team.state not in ["done", "open"]:
            raise PermissionDenied("In dieser Phase kann der Modus nicht geändert werden.")
            
        team.mode = mode
        team.save()
        return SetModeMutation(team=team)

class Mutation(ObjectType):
    next_phase = NextPhaseMutation.Field()
    post_question = PostQuestionMutation.Field()
    post_answer = PostAnswerMutation.Field()
    update_question = UpdateQuestionMutation.Field()
    score_answer = ScoreAnswerMutation.Field()
    create_team = CreateTeamMutation.Field()
    add_member = AddMemberMutation.Field()
    remove_member = RemoveMemberMutation.Field()
    remove_question = RemoveQuestionMutation.Field()
    set_mode = SetModeMutation.Field()


class Query(ObjectType):
    team = relay.Node.Field(TeamNode)
    topic = relay.Node.Field(TopicNode)
    question = relay.Node.Field(QuestionNode)

    topics = DjangoFilterConnectionField(TopicNode, filterset_class=TopicFilter)
    questions = DjangoFilterConnectionField(QuestionNode, filterset_class=QuestionFilter)
    teams = DjangoFilterConnectionField(TeamNode)
    users = DjangoFilterConnectionField(UserNode)

    me = graphene.Field(UserNode)

    @login_required
    def resolve_teams(self, info):
        return Team.objects.filter(members=info.context.user)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
