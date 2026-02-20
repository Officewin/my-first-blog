from django.db import models
from django.conf import settings
from django.utils import timezone


class PronunciationHistory(models.Model):
    """Store results of pronunciation API calls for each user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pronunciation_records"
    )
    text = models.CharField(max_length=255)
    response = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.user} - {self.text} ({self.created:%Y-%m-%d %H:%M:%S})"


class DailyPractice(models.Model):
    """Track each user's daily practice progress."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    words = models.JSONField()
    index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.user} {self.date} {self.index}/" f"{len(self.words)}"


class DailySubmission(models.Model):
    """Track how many practices a user submits per day."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.user} {self.date}: {self.count}"

