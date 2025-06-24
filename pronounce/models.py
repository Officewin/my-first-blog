from django.db import models
from django.conf import settings


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

