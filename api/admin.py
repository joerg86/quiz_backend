from django.contrib import admin
from .models import Team, Topic, Question, Answer, Membership


class AnswerInline(admin.StackedInline):
    model = Answer

class QuestionInline(admin.StackedInline):
    model = Question

class MembershipInline(admin.TabularInline):
    autocomplete_fields = ["user"]
    model = Membership

class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "creator", "created_at")
    search_fields = ("name",)
    autocomplete_fields = ["topic", "current_question", "creator"]

    inlines = [
        MembershipInline, QuestionInline
    ]

class QuestionAdmin(admin.ModelAdmin):
    list_display = ("author", "topic", "question", "created_at")
    search_fields = ("topic__name", "model_answer", "question", "team")
    autocomplete_fields = ("topic", "author", "team")

    inlines = [
        AnswerInline
    ]

class AnswerAdmin(admin.ModelAdmin):
    list_display =("author", "question", "answer", "created_at")
    autocomplete_fields = ["question"]

class TopicAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")

# Register your models here.
admin.site.register(Team, TeamAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)