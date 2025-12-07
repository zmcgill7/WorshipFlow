from django.db import models
from django.contrib.auth.models import User


class AnalysisResult(models.Model):
    """Stores audio file analysis results for a user"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Delete results if user is deleted
        related_name='analysis_results'
    )
    filename = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['user']),  # Speed up user history queries
        ]

    def __str__(self):
        return f"{self.filename} - {self.user.email}"


class InstrumentPrediction(models.Model):
    """Individual instrument prediction (>50% confidence) for an analysis result"""
    analysis_result = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,  # Delete predictions if parent result is deleted
        related_name='predictions'
    )
    instrument = models.CharField(max_length=100)
    confidence = models.FloatField()  # 0.0 to 1.0

    class Meta:
        ordering = ['-confidence']  # Highest confidence first

    def __str__(self):
        return f"{self.instrument} ({self.confidence:.1%})"
