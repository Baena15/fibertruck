"""
Debug middleware para Railway - devuelve errores como JSON
"""
import traceback
from django.http import JsonResponse


class DebugErrorMiddleware:
    """Captura excepciones y devuelve JSON con el traceback."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        tb = traceback.format_exc()
        return JsonResponse({
            'error': str(exception),
            'type': type(exception).__name__,
            'traceback': tb,
        }, status=500)
