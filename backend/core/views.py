from django.http import JsonResponse
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import tempfile
import os
import logging
import json

logger = logging.getLogger(__name__)


def getInstrumentsFromFile(file):
    predictor = apps.get_app_config('core').predictor
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        logger.info(f"Processing file: {file.name}")
        return predictor.predict(tmp_path, top_k=3)
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
