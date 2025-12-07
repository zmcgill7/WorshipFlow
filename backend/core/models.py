from django.db import models
from django.contrib.auth.models import User


class AnalysisResult(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Drop results if user is removed
        related_name='analysis_results'
    )
    filename = models.CharField(max_length=255)

    class Meta:
        indexes = [models.Index(fields=['user'])]  # Speed up user history queries

    def __str__(self):
        return f"{self.filename} - {self.user.email}"


class InstrumentPrediction(models.Model):
    analysis_result = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,  # Drop predictions if parent result is removed
        related_name='predictions'
    )
    instrument = models.CharField(max_length=100)
    confidence = models.FloatField()

    class Meta:
        ordering = ['-confidence']  # Highest confidence first

    def __str__(self):
        return f"{self.instrument} ({self.confidence:.1%})"
