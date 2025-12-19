from django.http import JsonResponse
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .middleware import firebase_auth_required
from firebase_admin import firestore
import tempfile
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

# Check if running in dev mode
DEV_MODE = os.environ.get('DJANGO_DEBUG') == 'True'


def getInstrumentsFromFile(file):
    predictor = apps.get_app_config('core').get_predictor()

    if predictor is None:
        logger.error("Predictor not available - model failed to load")
        raise ValueError("Model not available. Please contact support.")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        logger.info(f"Processing file: {file.name}")
        try:
            result = predictor.predict_file(
                tmp_path, return_probabilities=True)
        except BaseException as e:  # catch SystemExit and other non-Exception failures
            logger.error(
                f"Predictor failed for {file.name}: {e}", exc_info=True)
            raise ValueError(
                "Audio processing failed. Please try another file.")

        # Keep instruments above 50% confidence
        filtered_probs = [
            (instrument, confidence)
            for instrument, confidence in result['probabilities'].items()
            if confidence > 0.5
        ]

        # Highest confidence first
        sorted_probs = sorted(filtered_probs, key=lambda x: x[1], reverse=True)

        return [
            {'instrument': instrument, 'confidence': confidence}
            for instrument, confidence in sorted_probs
        ]
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@csrf_exempt
@require_http_methods(["POST"])
@firebase_auth_required
def analyzeFiles(httpRequest):
    uploadedFiles = httpRequest.FILES.getlist("file")
    if not uploadedFiles:
        return JsonResponse({"error": "No files uploaded"}, status=400)

    instrumentLists = []
    firestore_saves = []  # Defer Firestore operations until after all predictions

    for uploadedFile in uploadedFiles:
        try:
            instrumentList = getInstrumentsFromFile(uploadedFile)
            logger.info("Predicted instruments!")
            instrumentLists.append({
                "filename": uploadedFile.name,
                "predictions": instrumentList
            })

            # Queue Firestore save for later (unless in dev mode)
            if not DEV_MODE:
                firestore_saves.append((uploadedFile, instrumentList))

        except ValueError as ve:
            instrumentLists.append({
                "filename": uploadedFile.name,
                "error": str(ve)
            })

    # Save to Firestore after all predictions complete (skip in dev mode)
    if DEV_MODE:
        logger.info("DEV MODE: Skipping Firestore saves")
    else:
        user_uid = httpRequest.firebase_user['uid']
        db = apps.get_app_config('core').get_db()

        for uploaded_file, predictions in firestore_saves:
            try:
                # Calculate file hash for deduplication (hash of file content)
                file_hasher = hashlib.sha256()
                uploaded_file.seek(0)  # Reset file pointer
                for chunk in uploaded_file.chunks():
                    file_hasher.update(chunk)
                file_hash = file_hasher.hexdigest()

                # Check if this file hash already exists for this user
                analyses_ref = db.collection('users').document(user_uid).collection('analyses')
                existing = analyses_ref.where('file_hash', '==', file_hash).limit(1).get()

                if len(list(existing)) > 0:
                    logger.info(f"File {uploaded_file.name} already analyzed (hash: {file_hash})")
                    continue

                # Create analysis document
                analysis_data = {
                    'filename': uploaded_file.name,
                    'file_hash': file_hash,
                    'instruments': [pred['instrument'].lower() for pred in predictions],
                    'predictions': predictions,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }

                analyses_ref.add(analysis_data)
                logger.info(f"Saved analysis for {uploaded_file.name} to Firestore")

            except Exception as e:
                logger.error(f"Firestore save failed for {uploaded_file.name}: {e}", exc_info=True)
                # Continue processing other files even if one fails

    return JsonResponse({"results": instrumentLists}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
@firebase_auth_required
def get_history(request):
    # Get Firestore client (lazy initialization)
    db = apps.get_app_config('core').get_db()
    user_uid = request.firebase_user['uid']

    try:
        # Fetch all analyses for user
        analyses_ref = db.collection('users').document(user_uid).collection('analyses')
        analyses = list(analyses_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream())

        # Get filter parameters
        instruments_list = request.GET.get('instruments', '')
        filter_mode = request.GET.get('filterMode', 'none')

        history_data = []

        for doc in analyses:
            data = doc.to_dict()
            analysis_item = {
                'id': doc.id,
                'filename': data.get('filename', ''),
                'predictions': data.get('predictions', [])
            }
            history_data.append(analysis_item)

        # Client-side filtering (Firestore limitations)
        if instruments_list and filter_mode != 'none':
            instruments = [inst.strip().lower()
                           for inst in instruments_list.split(',') if inst.strip()]

            if instruments:
                if filter_mode == 'exclude':
                    # Exclude analyses that contain ANY of the specified instruments
                    history_data = [
                        item for item in history_data
                        if not any(
                            inst in [p['instrument'].lower() for p in item['predictions']]
                            for inst in instruments
                        )
                    ]
                elif filter_mode == 'require':
                    # Require analyses that contain ALL of the specified instruments
                    history_data = [
                        item for item in history_data
                        if all(
                            any(inst == p['instrument'].lower() for p in item['predictions'])
                            for inst in instruments
                        )
                    ]

        return JsonResponse({'results': history_data}, status=200)

    except Exception as e:
        logger.error(f"Failed to fetch history: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to fetch history'}, status=500)
