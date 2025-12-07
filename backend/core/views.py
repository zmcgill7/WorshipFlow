from django.http import JsonResponse
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import AnalysisResult, InstrumentPrediction
import tempfile
import os
import logging
import json

logger = logging.getLogger(__name__)


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
def analyzeFiles(httpRequest):
    uploadedFiles = httpRequest.FILES.getlist("file")
    if not uploadedFiles:
        return JsonResponse({"error": "No files uploaded"}, status=400)

    instrumentLists = []
    db_saves = []  # Defer database operations until after all predictions

    for uploadedFile in uploadedFiles:
        try:
            instrumentList = getInstrumentsFromFile(uploadedFile)
            logger.info("Predicted instruments!")
            instrumentLists.append({
                "filename": uploadedFile.name,
                "predictions": instrumentList
            })

            # Queue database save for later
            if httpRequest.user.is_authenticated:
                db_saves.append((uploadedFile.name, instrumentList))

        except ValueError as ve:
            instrumentLists.append({
                "filename": uploadedFile.name,
                "error": str(ve)
            })

    # Save to database after all predictions complete
    if httpRequest.user.is_authenticated:
        for filename, predictions in db_saves:
            # Skip if this filename already exists for this user
            if AnalysisResult.objects.filter(user=httpRequest.user, filename=filename).exists():
                continue

            analysis_result = AnalysisResult.objects.create(
                user=httpRequest.user,
                filename=filename
            )
            for pred in predictions:
                InstrumentPrediction.objects.create(
                    analysis_result=analysis_result,
                    instrument=pred['instrument'],
                    confidence=pred['confidence']
                )

    return JsonResponse({"results": instrumentLists}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return JsonResponse(
            {"error": "Name, email, and password are required."}, status=400
        )

    if User.objects.filter(email=email).exists():
        return JsonResponse(
            {"error": "A user with this email already exists."}, status=400
        )

    # Use email as the username to keep things simple
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name,
    )

    auth_login(request, user)

    return JsonResponse(
        {
            "id": user.id,
            "name": user.first_name or user.username,
            "email": user.email,
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return JsonResponse(
            {"error": "Email and password are required."}, status=400
        )

    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({"error": "Invalid email or password."}, status=400)

    auth_login(request, user)

    return JsonResponse(
        {
            "id": user.id,
            "name": user.first_name or user.username,
            "email": user.email,
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    auth_logout(request)
    return JsonResponse({"success": True}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def get_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    results = AnalysisResult.objects.filter(
        user=request.user).prefetch_related('predictions')

    instruments_list = request.GET.get('instruments', '')
    filter_mode = request.GET.get('filterMode', 'none')

    if instruments_list and filter_mode != 'none':
        instruments = [inst.strip()
                       for inst in instruments_list.split(',') if inst.strip()]

        if instruments:
            if filter_mode == 'exclude':
                for instrument in instruments:
                    results = results.exclude(
                        predictions__instrument__iexact=instrument)
            elif filter_mode == 'require':
                for instrument in instruments:
                    results = results.filter(
                        predictions__instrument__iexact=instrument)
                results = results.distinct()

    history_data = []
    for result in results:
        history_data.append({
            'id': result.id,
            'filename': result.filename,
            'predictions': [
                {
                    'instrument': pred.instrument,
                    'confidence': pred.confidence
                }
                for pred in result.predictions.all()
            ]
        })

    return JsonResponse({'results': history_data}, status=200)
