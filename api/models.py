from django.db import models
from django.db.models import Sum

# Create your models here.
class Topic(models.Model):
    name = models.CharField("Name", max_length=100)
    code = models.CharField("Code", max_length=20, unique=True)

    def __str__(self):
        return f"{self.code} {self.name}"

    class Meta:
        verbose_name = "Thema"
        verbose_name_plural = "Themen"

        ordering = ("code",)

class Question(models.Model):
    team = models.ForeignKey("Team", null=True, blank=True, on_delete=models.SET_NULL, related_name="questions")
    author = models.ForeignKey("auth.User", verbose_name="Autor", on_delete=models.CASCADE)
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE)
    question = models.TextField("Frage")
    model_answer = models.TextField("Musterantwort")
    done = models.BooleanField("Erledigt", help_text="Frage wurde von allen beantwortet", default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Frage"
        verbose_name_plural = "Fragen"

        unique_together = ("team", "author")

SCORE_CHOICES = (
    (0, "falsch"),
    (1, "teilweise richtig"),
    (3, "richtig")
)
class Answer(models.Model):
    author = models.ForeignKey("auth.User", verbose_name="Autor", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", verbose_name="Frage", on_delete=models.CASCADE)
    answer = models.TextField("Antwort")
    score = models.PositiveIntegerField("Bewertung", choices=SCORE_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    def __str__(self):
        return self.answer

    class Meta:
        verbose_name = "Antwort"
        verbose_name_plural = "Antworten"
        unique_together = ("author", "question")

STATE_CHOICES = (
    ("open", "offen"),
    ("question", "Erarbeitungsphase"),
    ("answer", "Fragephase"),
    ("scoring", "Bewertungsphase"),
    ("done", "Abgeschlossen"),
    ("archived", "archiviert")

)
MODE_CHOICES = (
    ("train", "Training"),
    ("competition", "Wettkampf")
)
class Team(models.Model):
    creator = models.ForeignKey("auth.User", related_name="teams_as_creator", on_delete=models.CASCADE, verbose_name="Gründer")
    topic = models.ForeignKey("Topic", verbose_name="Thema", on_delete=models.CASCADE)
    name = models.CharField("Name", max_length=100)
    members = models.ManyToManyField("auth.User", related_name="teams", verbose_name="Mitglieder", through="Membership")

    current_question = models.ForeignKey("Question", on_delete=models.SET_NULL, related_name="team_current_set", verbose_name="Aktuelle Frage", null=True, blank=True)

    state = models.CharField("Status", max_length=30, choices=STATE_CHOICES, default="open")
    mode = models.CharField("Modus", max_length=30, choices=MODE_CHOICES, default="train")

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    def next_state(self):
        """Return the next state of the team"""

        if self.state in ["open", "done"] and self.members.count() > 1:
            self.questions.clear()
            self.membership_set.update(partial=0,wrong=0,right=0)
            self.state = "question"

        if self.state == "scoring":
            for ms in self.membership_set.all():
                scores = Answer.objects.filter(author=ms.user, question__team=self)
                
                ms.partial = scores.filter(score=1).count()
                ms.right = scores.filter(score=3).count()
                ms.wrong = scores.filter(score=0).count()
                ms.save()

            self.current_question.done = True
            self.current_question.save()

            self.current_question = self.questions.filter(answer=None).first()
            if self.current_question:
                self.state = "answer"
            else:
                self.state = "done"
        
        self.save()

    def user_done(self, user):
        """Checks if user is done for this phase"""
        if self.state == "question":
            return self.questions.filter(author=user).count() > 0
        if self.state == "answer":
            if self.current_question:
                if self.current_question.author == user:
                    return True
                return self.current_question.answer_set.filter(author=user).count() > 0
            return False            

    def get_user_question(self, user):
        """Get the question that was submitted by the specified user."""
        return self.questions.filter(author=user).first()

    def get_user_answer(self, user):
        """Get the answer to the current question submitted by the user."""
        return self.current_question.answer_set.filter(author=user).first()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"

class Membership(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    team = models.ForeignKey("Team", on_delete=models.CASCADE)

    right = models.PositiveIntegerField("richtig", default=0)
    partial = models.PositiveIntegerField("tlw. richtig", default=0)
    wrong = models.PositiveIntegerField("falsch", default=0)

    joined = models.DateTimeField(auto_now_add=True)

    def get_score(self):
        return self.right * 3 + self.partial * 1

    class Meta:
        verbose_name = "Mitgliedschaft"
        verbose_name_plural = "Mitgliedschaften"

        unique_together = ("user", "team")