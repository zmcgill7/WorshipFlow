from django.apps import AppConfig
from pathlib import Path
import logging


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    predictor = None  # Singleton instance

    def ready(self):
        """Called when Django starts - warm up database connection"""
        from django.db import connection
        try:
            # Force database connection at startup to avoid first-request timeout
            connection.ensure_connection()
        except Exception:
            pass  # Connection will be retried on first request

    @classmethod
    def get_predictor(cls):
        """Load model lazily on first use."""
        if cls.predictor is not None:
            return cls.predictor

        logger = logging.getLogger(__name__)
        try:
            from .model_utils.predict_v2 import InstrumentClassifier

            model_dir = Path(__file__).parent / 'model_utils'
            cls.predictor = InstrumentClassifier(
                model_path=str(model_dir / 'best_model.keras'),
                results_path=str(model_dir / 'training_results.json'),
                yamnet_path=str(model_dir / 'yamnet'),
            )
            logger.info("WorshipFlow model loaded successfully.")
        except Exception:
            logger.error(
                "Failed to load WorshipFlow model; /api/analyze/ will be disabled.",
                exc_info=True,
            )
            cls.predictor = None

        return cls.predictor
