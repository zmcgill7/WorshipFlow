from django.apps import AppConfig
from pathlib import Path
import logging
import firebase_admin
from firebase_admin import firestore


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    predictor = None  # Singleton instance
    db = None  # Firestore client singleton

    def ready(self):
        """Called when Django starts - initialize Firebase and Firestore"""
        logger = logging.getLogger(__name__)

        # Try to initialize Firebase - will fail during collectstatic (no credentials)
        # but succeed when actually running the server
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app()

            # Initialize Firestore client
            CoreConfig.db = firestore.client()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            # This is expected during Docker build (collectstatic) or local dev without credentials
            logger.info(f"Firebase initialization skipped (will retry on first request): {e}")
            CoreConfig.db = None

        # Start loading model in background thread
        # import threading
        # threading.Thread(target=self.get_predictor, daemon=True).start()

    @classmethod
    def get_db(cls):
        """Get Firestore client, initializing if needed"""
        if cls.db is not None:
            return cls.db

        logger = logging.getLogger(__name__)
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            cls.db = firestore.client()
            logger.info("Firestore client initialized on first use")
            return cls.db
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}", exc_info=True)
            raise

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
