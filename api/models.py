from django.db import models

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
    round = models.ForeignKey("Round", verbose_name="Runde", on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey("auth.User", verbose_name="Autor", on_delete=models.CASCADE)
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE)
    question = models.TextField("Frage")
    model_answer = models.TextField("Musterantwort")


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Frage"
        verbose_name_plural = "Fragen"

SCORE_CHOICES = (
    (0, "falsch"),
    (1, "teilweise richtig"),
    (3, "richtig")
)
class Answer(models.Model):
    author = models.ForeignKey("auth.User", verbose_name="Autor", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", verbose_name="Frage", on_delete=models.CASCADE)
    answer = models.TextField("Antwort")
    score = models.PositiveIntegerField("Bewertung", choices=SCORE_CHOICES)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    def __str__(self):
        return self.answer

    class Meta:
        verbose_name = "Antwort"
        verbose_name_plural = "Antworten"

STATE_CHOICES = (
    ("open", "offen"),
    ("playing", "spielt"),
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
    members = models.ManyToManyField("auth.User", related_name="teams", verbose_name="Mitglieder")

    state = models.CharField("Status", max_length=30, choices=STATE_CHOICES, default="open")
    mode = models.CharField("Modus", max_length=30, choices=MODE_CHOICES, default="train")

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"

PHASE_CHOICES = (
    ("question", "Erarbeitungsphase"),
    ("answer", "Fragephase"),
    ("scoring", "Bewertungsphase"),
    ("done", "Abgeschlossen"),
)

class Round(models.Model):
    team = models.ForeignKey("Team", on_delete=models.CASCADE, verbose_name="Team")
    current_question = models.ForeignKey("Question", on_delete=models.CASCADE, related_name="round_current_set", verbose_name="Aktuelle Frage", null=True, blank=True)

    phase = models.CharField("Phase", max_length=30, choices=PHASE_CHOICES, default="question")
    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Runde"
        verbose_name_plural = "Runden"