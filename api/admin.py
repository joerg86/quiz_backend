from django.contrib import admin
from .models import Team, Topic, Round, Question, Answer


class AnswerInline(admin.StackedInline):
    model = Answer

class RoundInline(admin.StackedInline):
    model = Round

class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "creator", "created_at")
    search_fields = ("name",)

    inlines = [
        RoundInline,
    ]

class QuestionAdmin(admin.ModelAdmin):
    list_display = ("author", "topic", "question", "created_at")
    search_fields = ("topic__name", "model_answer", "question")

    inlines = [
        AnswerInline
    ]

class AnswerAdmin(admin.ModelAdmin):
    list_display =("author", "question", "answer", "created_at")

class TopicAdmin(admin.ModelAdmin):
    list_display = ("code", "name")

# Register your models here.
admin.site.register(Team, TeamAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Round)
admin.site.register(Answer)