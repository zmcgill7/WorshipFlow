from django.apps import AppConfig
from pathlib import Path
import logging


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    predictor = None  # Singleton instance

    def ready(self):
        """Load model once at startup.

        If the model or TensorFlow stack cannot be loaded (e.g., on a
        development machine without the correct native dependencies), the
        exception is logged and the backend continues to function. In that
        case, the /api/analyze/ endpoint will return errors when called,
        but other features (like auth) will still work.
        """
        if CoreConfig.predictor is not None:
            return

        logger = logging.getLogger(__name__)
        try:
            from .model_utils.predict import WorshipFlowPredictor

            model_dir = Path(__file__).parent / 'model_utils'
            CoreConfig.predictor = WorshipFlowPredictor(
                model_path=str(model_dir / 'best_model.keras'),
                config_path=str(model_dir / 'training_results.json'),
            )
            logger.info("WorshipFlow model loaded successfully.")
        except Exception:
            # Log the full stack trace but don't crash the app in dev
            logger.error(
                "Failed to load WorshipFlow model; /api/analyze/ will be disabled.",
                exc_info=True,
            )
            CoreConfig.predictor = None
