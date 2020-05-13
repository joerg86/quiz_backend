from django.db.models.signals import post_save, post_delete, m2m_changed
from graphene_subscriptions.signals import post_save_subscription, post_delete_subscription

from .models import Team

post_save.connect(post_save_subscription, sender=Team, dispatch_uid="team_post_save")
post_delete.connect(post_delete_subscription, sender=Team, dispatch_uid="team_post_delete")

def m2m_question(sender, instance, **kwargs):
    print("M2M changed  ")
    post_save_subscription(Team, instance, False, **kwargs)

m2m_changed.connect(m2m_question, sender=Team.questions.through, dispatch_uid="team_question_post")