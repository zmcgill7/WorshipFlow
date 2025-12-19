from firebase_admin import auth
from django.http import JsonResponse
import functools
import os
import logging

logger = logging.getLogger(__name__)

def firebase_auth_required(view_func):
    """Decorator to verify Firebase ID token and attach user to request"""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # DEV MODE: Skip authentication if DJANGO_DEBUG=True
        if os.environ.get('DJANGO_DEBUG') == 'True':
            logger.info("DEV MODE: Bypassing Firebase auth, using mock user")
            request.firebase_user = {
                'uid': 'local-dev-user-123',
                'email': 'dev@localhost',
                'name': 'Local Dev User'
            }
            return view_func(request, *args, **kwargs)

        # PRODUCTION: Verify Firebase token
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Missing authentication token'}, status=401)

        id_token = auth_header.split('Bearer ')[1]

        try:
            decoded_token = auth.verify_id_token(id_token)
            # Attach Firebase user info to request
            # decoded_token contains: uid, email, name, etc.
            request.firebase_user = decoded_token
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return JsonResponse({'error': 'Invalid authentication token'}, status=401)

    return wrapper
