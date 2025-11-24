from django.http import JsonResponse
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import tempfile
import os
import logging

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
