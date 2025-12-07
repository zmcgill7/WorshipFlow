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
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        logger.info(f"Processing file: {file.name}")
        result = predictor.predict_file(tmp_path, return_probabilities=True)

        # Convert new format to old format for backward compatibility
        # Return all instruments with confidence > 50%
        filtered_probs = [
            (instrument, confidence)
            for instrument, confidence in result['probabilities'].items()
            if confidence > 0.5
        ]

        # Sort by probability (highest first)
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
    """Analyze uploaded audio files and return instrument predictions"""
    try:
        uploadedFiles = httpRequest.FILES.getlist("file")
        if not uploadedFiles:
            return JsonResponse({"error": "No files uploaded"}, status=400)

        if len(uploadedFiles) > 10:
            return JsonResponse(
                {"error": "Too many files. Maximum 10 files allowed."},
                status=400
            )

        instrumentLists = []
        for uploadedFile in uploadedFiles:
            try:
                # Perform analysis on the uploaded files
                instrumentList = getInstrumentsFromFile(uploadedFile)

                # Save to database if user is authenticated
                if httpRequest.user.is_authenticated:
                    analysis_result = AnalysisResult.objects.create(
                        user=httpRequest.user,
                        filename=uploadedFile.name
                    )

                    # Save predictions (only those above 50% confidence are returned from predictor)
                    for pred in instrumentList:
                        InstrumentPrediction.objects.create(
                            analysis_result=analysis_result,
                            instrument=pred['instrument'],
                            confidence=pred['confidence']
                        )

                instrumentLists.append({
                    "filename": uploadedFile.name,
                    "predictions": instrumentList
                })
            except ValueError as ve:
                logger.warning(
                    f"Validation error for {uploadedFile.name}: {ve}")
                instrumentLists.append({
                    "filename": uploadedFile.name,
                    "error": str(ve)
                })
            except Exception as e:
                logger.error(
                    f"Error processing {uploadedFile.name}: {e}", exc_info=True)
                instrumentLists.append({
                    "filename": uploadedFile.name,
                    "error": "Failed to process file"
                })

        return JsonResponse({"results": instrumentLists}, status=200)

    except Exception as e:
        logger.error(f"Unexpected error in analyzeFiles: {e}", exc_info=True)
        return JsonResponse(
            {"error": "Internal server error"},
            status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    """Create a new user account using Django's auth system."""
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
    """Log in an existing user using email and password."""
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
    """Log out the current user (if any)."""
    auth_logout(request)
    return JsonResponse({"success": True}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def get_history(request):
    """Get analysis history for the authenticated user"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Get query parameters for filtering
    instrument_filter = request.GET.get('instrument')  # Optional: filter by instrument
    search_query = request.GET.get('search')  # Optional: search filenames
    limit = min(int(request.GET.get('limit', 1000)), 1000)  # Max 1000 results

    # Build query
    results = AnalysisResult.objects.filter(user=request.user)

    if instrument_filter:
        results = results.filter(predictions__instrument__iexact=instrument_filter).distinct()

    if search_query:
        results = results.filter(filename__icontains=search_query)

    # Limit results
    results = results[:limit]

    # Serialize data
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
