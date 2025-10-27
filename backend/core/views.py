from django.http import JsonResponse

# Create your views here.


def getInstrumentsFromFile(file):
    # Dummy implementation for illustration
    # Will be replaced by model inference logic
    return ["guitar", "piano", "drums"]


def analyzeFiles(httpRequest):
    uploadedFiles = httpRequest.FILES.getlist("file")
    if not uploadedFiles:
        return JsonResponse({"error": "No files uploaded"}, status=400)
    instrumentLists = []
    for uploadedFile in uploadedFiles:
        # Perform analysis on the uploaded files
        instrumentList = getInstrumentsFromFile(uploadedFile)
        instrumentLists.append(instrumentList)

    return JsonResponse({"instruments": instrumentLists}, status=200)
