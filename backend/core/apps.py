from django.apps import AppConfig
from pathlib import Path


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    predictor = None  # Singleton instance

    def ready(self):
        """Load model once at startup"""
        if CoreConfig.predictor is None:
            from .model_utils.predict import WorshipFlowPredictor

            model_dir = Path(__file__).parent / 'model_utils'
            CoreConfig.predictor = WorshipFlowPredictor(
                model_path=str(model_dir / 'best_model.keras'),
                config_path=str(model_dir / 'training_results.json')
            )
