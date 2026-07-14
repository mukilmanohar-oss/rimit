from rest_framework.views import exception_handler
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If it's a Django ValidationError (which normally causes a 500 error in DRF),
    # catch it and convert it to a 400 Bad Request response.
    if isinstance(exc, DjangoValidationError):
        data = exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages}
        return Response(data, status=400)

    return response
